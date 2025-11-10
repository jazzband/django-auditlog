import contextlib
import datetime
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, transaction

from auditlog.models import LogEntry


@dataclass(frozen=True)
class PartitionBounds:
    lower: datetime.datetime
    upper: datetime.datetime

    @property
    def name_suffix(self) -> str:
        return f"{self.lower:%Y_%m}"


class Command(BaseCommand):
    help = "Manage PostgreSQL range partitions for auditlog's LogEntry table."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand")
        subparsers.required = True

        init_parser = subparsers.add_parser(
            "init",
            help=(
                "Create the partitioned parent table (empty or populated via --convert). "
                "Only supported on PostgreSQL."
            ),
        )
        self._add_common_db_argument(init_parser)
        init_parser.add_argument(
            "--ahead",
            type=int,
            default=None,
            help="Number of future months to create partitions for "
            "(defaults to AUDITLOG_PARTITION_AHEAD_MONTHS).",
        )
        init_parser.add_argument(
            "--retention-months",
            type=int,
            default=None,
            help="Optional retention window in months; used with --convert to pre-create partitions "
            "covering the retention horizon plus ahead months "
            "defaults to AUDITLOG_PARTITION_RETENTION_MONTHS).",
        )
        init_parser.add_argument(
            "--convert",
            action="store_true",
            help=(
                "Best-effort conversion when the table already contains rows. Requires downtime "
                "and runs a full COPY into the partitioned parent."
            ),
        )

        create_parser = subparsers.add_parser(
            "create",
            help="Create monthly partitions for the configured interval.",
        )
        self._add_common_db_argument(create_parser)
        create_parser.add_argument(
            "--start",
            type=_parse_year_month,
            default=None,
            help="Start month inclusive (YYYY-MM). Defaults to current month.",
        )
        create_parser.add_argument(
            "--end",
            type=_parse_year_month,
            default=None,
            help="End month exclusive (YYYY-MM). Defaults to start + ahead months.",
        )
        create_parser.add_argument(
            "--ahead",
            type=int,
            default=None,
            help="If start/end omitted, create this many months ahead of the current month "
            "(defaults to AUDITLOG_PARTITION_AHEAD_MONTHS).",
        )

        prune_parser = subparsers.add_parser(
            "prune",
            help="Drop partitions older than the retention window.",
        )
        self._add_common_db_argument(prune_parser)
        prune_parser.add_argument(
            "--retention-months",
            type=int,
            default=None,
            help="Retention window in months. Defaults to AUDITLOG_PARTITION_RETENTION_MONTHS.",
        )
        prune_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show partitions that would be dropped without executing.",
        )

        status_parser = subparsers.add_parser(
            "status",
            help="Display partitioning status and existing partitions.",
        )
        self._add_common_db_argument(status_parser)

    def _add_common_db_argument(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Database alias to operate on.",
        )

    def handle(self, *args, **options):
        subcommand = options.pop("subcommand")
        database = options.pop("database", DEFAULT_DB_ALIAS)
        connection = self._get_postgres_connection(database)
        table = LogEntry._meta.db_table

        if subcommand == "init":
            self._handle_init(connection, table, **options)
        elif subcommand == "create":
            self._handle_create(connection, table, **options)
        elif subcommand == "prune":
            self._handle_prune(connection, table, **options)
        elif subcommand == "status":
            self._handle_status(connection, table, **options)
        else:
            raise CommandError(f"Unknown subcommand: {subcommand}")

    def _handle_init(
        self,
        connection,
        table: str,
        *,
        ahead: int | None,
        retention_months: int | None,
        convert: bool,
        **_,
    ):
        if self._is_partitioned(connection, table):
            self.stdout.write("Table is already partitioned; no action taken.")
            return

        ahead = _coalesce_int(ahead, settings.AUDITLOG_PARTITION_AHEAD_MONTHS)
        retention_months = _coalesce_int(
            retention_months, settings.AUDITLOG_PARTITION_RETENTION_MONTHS
        )
        if ahead is not None and ahead < 0:
            raise CommandError("Ahead months must be zero or positive.")
        if retention_months is not None and retention_months < 0:
            raise CommandError("Retention months must be zero or positive.")

        if not self._table_exists(connection, table):
            raise CommandError(
                f"Table '{table}' does not exist. Run migrations before partitioning."
            )

        schema, base_table = _split_schema_name(table)
        old_table_base = f"{base_table}_old"
        old_table = _qualified_name(schema, old_table_base)
        shadow_table = _qualified_name(schema, f"{base_table}_shadow")

        self._ensure_table_absent(connection, old_table)

        if convert:
            self._ensure_table_absent(connection, shadow_table)
            row_count = self._table_rowcount(connection, table)
            if row_count == 0:
                self.stdout.write(
                    "Table is empty; falling back to safe initialization."
                )
                convert = False
            else:
                self._convert_existing_table(
                    connection=connection,
                    table=table,
                    schema=schema,
                    base_table=base_table,
                    shadow_table=shadow_table,
                    old_table=old_table,
                    old_table_base=old_table_base,
                    ahead=ahead,
                    retention_months=retention_months,
                    row_count=row_count,
                )
                self.stdout.write("Partitioning initialized successfully.")
                return

        self._initialize_empty_table(
            connection=connection,
            table=table,
            schema=schema,
            base_table=base_table,
            old_table=old_table,
            ahead=ahead,
            retention_months=retention_months,
        )
        self.stdout.write("Partitioning initialized successfully.")

    def _initialize_empty_table(
        self,
        connection,
        table: str,
        schema: str | None,
        base_table: str,
        old_table: str,
        ahead: int | None,
        retention_months: int | None,
    ):
        row_count = self._table_rowcount(connection, table)
        if row_count != 0:
            raise CommandError(
                "Table is not empty. Use --convert to perform best-effort conversion."
            )

        partition_months = self._collect_partition_months(
            bounds=None,
            ahead=ahead,
            retention_months=retention_months,
        )
        partitions = [_partition_bounds_for_month(month) for month in partition_months]

        with transaction.atomic(using=connection.alias):
            self._lock_table(connection, table)
            self._rename_table(connection, table, f"{base_table}_old")
            self._create_partitioned_parent(connection, table, old_table)

            all_indexes = list(self._indexed_columns(connection))
            for partition in partitions:
                self._create_partition(connection, table, partition)

            self._create_partition_indexes(connection, table, all_indexes)
            sequence_name = self._prepare_sequence(connection, table, old_table)
            if sequence_name:
                self._reset_sequence(connection, table, sequence_name, empty=True)

            self._drop_table(connection, old_table)

    def _convert_existing_table(
        self,
        connection,
        table: str,
        schema: str | None,
        base_table: str,
        shadow_table: str,
        old_table: str,
        old_table_base: str,
        ahead: int | None,
        retention_months: int | None,
        row_count: int,
    ):
        bounds = self._timestamp_bounds(connection, table)
        if bounds is None:
            raise CommandError("Unable to determine timestamp bounds for conversion.")

        partition_months = self._collect_partition_months(
            bounds=bounds,
            ahead=ahead,
            retention_months=retention_months,
        )
        partitions = [_partition_bounds_for_month(month) for month in partition_months]
        initial_max_id = self._table_max_id(connection, table)
        sequence = self._sequence_name(connection, table)

        self.stdout.write(
            f"Converting populated table with approximately {row_count} rows. "
            "Minimal-downtime swap in progress..."
        )

        shadow_created = False
        try:
            self._create_partitioned_parent(connection, shadow_table, table)
            shadow_created = True

            all_indexes = list(self._indexed_columns(connection))
            for partition in partitions:
                self._create_partition(connection, shadow_table, partition)

            self._create_partition_indexes(connection, shadow_table, all_indexes)
            if sequence:
                self._set_sequence_default(connection, shadow_table, sequence)

            self._copy_table_to_shadow(
                connection=connection,
                source_table=table,
                target_table=shadow_table,
                partitions=partitions,
                max_id_snapshot=initial_max_id,
            )

            with transaction.atomic(using=connection.alias):
                self._lock_table(connection, table)
                self._lock_table(connection, shadow_table)

                self._sync_delta_rows(
                    connection=connection,
                    source_table=table,
                    target_table=shadow_table,
                    last_copied_id=initial_max_id,
                )

                self._ensure_table_absent(connection, old_table)

                self._rename_table(connection, table, old_table_base)
                self._rename_table(connection, shadow_table, base_table)
                shadow_created = False

                new_table = _qualified_name(schema, base_table)
                if sequence:
                    self._assign_sequence_owner(connection, sequence, new_table)
                    self._set_sequence_default(connection, new_table, sequence)
                    self._reset_sequence(connection, new_table, sequence)
                else:
                    new_sequence = self._sequence_name(connection, new_table)
                    if new_sequence:
                        self._reset_sequence(connection, new_table, new_sequence)

                self._drop_table(connection, old_table)
        finally:
            if shadow_created:
                self._drop_table_if_exists(connection, shadow_table)

    def _handle_create(
        self,
        connection,
        table: str,
        *,
        start: datetime.date | None,
        end: datetime.date | None,
        ahead: int | None,
        **_,
    ):
        if not self._is_partitioned(connection, table):
            raise CommandError(
                "Table is not partitioned. Run 'auditlogpartition init' first."
            )

        ahead = _coalesce_int(ahead, settings.AUDITLOG_PARTITION_AHEAD_MONTHS)
        if ahead is not None and ahead < 0:
            raise CommandError("Ahead months must be zero or positive.")
        today_month = _month_start(datetime.date.today())
        start_month = start or today_month
        if end:
            end_month = end
        else:
            ahead_value = max(ahead or 0, 0)
            end_month = _add_months(start_month, ahead_value + 1)

        if end_month <= start_month:
            raise CommandError("End month must be after start month.")

        created = 0
        for month in _iter_months(start_month, end_month, inclusive=False):
            partition = _partition_bounds_for_month(month)
            if self._create_partition(connection, table, partition):
                created += 1

        if created:
            self.stdout.write(f"Created {created} partition(s).")
        else:
            self.stdout.write("No new partitions were created.")

    def _handle_prune(
        self,
        connection,
        table: str,
        *,
        retention_months: int | None,
        dry_run: bool,
        **_,
    ):
        if not self._is_partitioned(connection, table):
            raise CommandError(
                "Table is not partitioned. Run 'auditlogpartition init' first."
            )

        retention_months = _coalesce_int(
            retention_months, settings.AUDITLOG_PARTITION_RETENTION_MONTHS
        )
        if retention_months is None:
            raise CommandError(
                "Retention window is not configured. Provide --retention-months "
                "or set AUDITLOG_PARTITION_RETENTION_MONTHS."
            )
        if retention_months <= 0:
            raise CommandError("Retention months must be greater than zero.")

        cutoff_month = _add_months(
            _month_start(datetime.date.today()), -retention_months
        )
        partitions = list(self._list_partitions(connection, table))
        drop_candidates = [p for p in partitions if p.lower.date() < cutoff_month]

        if not drop_candidates:
            self.stdout.write("No partitions eligible for pruning.")
            return

        if dry_run:
            self.stdout.write("Partitions that would be dropped:")
            for part in drop_candidates:
                self.stdout.write(
                    f"  - {self._partition_name(table, part)} "
                    f"[{part.lower.isoformat()} → {part.upper.isoformat()})"
                )
            return

        for part in drop_candidates:
            self._drop_partition(connection, table, part)

        self.stdout.write(f"Dropped {len(drop_candidates)} partition(s).")

    def _handle_status(self, connection, table: str, **_):
        partitioned = self._is_partitioned(connection, table)
        if not partitioned:
            self.stdout.write("Partitioned: no")
            return

        self.stdout.write("Partitioned: yes")
        partitions = list(self._list_partitions(connection, table))
        if not partitions:
            self.stdout.write("No partitions found.")
            return

        self.stdout.write("Partitions:")
        for part in partitions:
            name = self._partition_name(table, part)
            self.stdout.write(
                f"  - {name} [{part.lower.isoformat()} → {part.upper.isoformat()})"
            )

    def _get_postgres_connection(self, alias: str):
        try:
            connection = connections[alias]
        except KeyError:
            raise CommandError(f"Unknown database alias '{alias}'.")

        if connection.vendor != "postgresql":
            raise CommandError(
                f"auditlogpartition only supports PostgreSQL. Database '{alias}' "
                f"uses vendor '{connection.vendor}'."
            )
        return connection

    def _lock_table(self, connection, table: str):
        with connection.cursor() as cursor:
            cursor.execute(
                f"LOCK TABLE {self._qn(connection, table)} IN ACCESS EXCLUSIVE MODE;"
            )

    def _rename_table(self, connection, table: str, new_base_name: str):
        if "." in new_base_name:
            raise CommandError("New table name must not include a schema qualifier.")
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE {table} RENAME TO {name};".format(
                    table=self._qn(connection, table),
                    name=connection.ops.quote_name(new_base_name),
                )
            )

    def _create_partitioned_parent(self, connection, table: str, old_table: str):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE {self._qn(connection, table)} (
                    LIKE {self._qn(connection, old_table)}
                        INCLUDING DEFAULTS
                        INCLUDING GENERATED
                        INCLUDING STORAGE
                        INCLUDING COMMENTS
                )
                PARTITION BY RANGE (timestamp);
                """
            )

    def _create_partition_indexes(self, connection, table: str, columns: Iterable[str]):
        base_table = _base_table_name(table)
        for column in columns:
            index_name = f"{base_table}_{column}_idx"
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {self._qn(connection, index_name)} "
                    f"ON {self._qn(connection, table)} ({self._qn(connection, column, allow_schema=False)});"
                )

    def _prepare_sequence(self, connection, table: str, old_table: str) -> str | None:
        sequence = self._sequence_name(connection, old_table)
        if not sequence:
            return None

        target = self._target_sequence_name(sequence, table)
        if target != sequence:
            sequence = self._rename_sequence(connection, sequence, target)

        self._assign_sequence_owner(connection, sequence, table)
        self._set_sequence_default(connection, table, sequence)
        return sequence

    def _bulk_copy_into_parent(self, connection, table: str, old_table: str):
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {self._qn(connection, table)} SELECT * FROM {self._qn(connection, old_table)};"
            )

    def _assign_sequence_owner(self, connection, sequence: str, table: str):
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER SEQUENCE {self._qn(connection, sequence)} OWNED BY {self._qn(connection, table)}.id;"
            )

    def _set_sequence_default(self, connection, table: str, sequence: str):
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {self._qn(connection, table)} ALTER COLUMN id SET DEFAULT nextval(%s);",
                [sequence],
            )

    def _reset_sequence(
        self, connection, table: str, sequence: str, empty: bool = False
    ):
        with connection.cursor() as cursor:
            if empty:
                cursor.execute(
                    "SELECT setval(%s, 1, false);",
                    [sequence],
                )
            else:
                cursor.execute(
                    "SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table}), 1), true);".format(
                        table=self._qn(connection, table)
                    ),
                    [sequence],
                )

    def _drop_table(self, connection, table: str):
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {self._qn(connection, table)};")

    def _create_partition(
        self, connection, table: str, partition: PartitionBounds
    ) -> bool:
        partition_name = self._partition_name(table, partition)
        if self._table_exists(connection, partition_name):
            return False

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE {self._qn(connection, partition_name)} PARTITION OF {self._qn(connection, table)}
                FOR VALUES FROM (%s) TO (%s);
                """,
                [partition.lower, partition.upper],
            )
        return True

    def _drop_partition(self, connection, table: str, partition: PartitionBounds):
        partition_name = self._partition_name(table, partition)
        with connection.cursor() as cursor:
            cursor.execute(
                f"DROP TABLE IF EXISTS {self._qn(connection, partition_name)};"
            )

    def _partition_name(self, table: str, partition: PartitionBounds) -> str:
        schema, base = _split_schema_name(table)
        name = f"{base}_{partition.name_suffix}"
        return f"{schema}.{name}" if schema else name

    def _table_exists(self, connection, table: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass(%s) IS NOT NULL;",
                [table],
            )
            return cursor.fetchone()[0]

    def _is_partitioned(self, connection, table: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_partitioned_table WHERE partrelid = %s::regclass);",
                [table],
            )
            return cursor.fetchone()[0]

    def _list_partitions(self, connection, table: str) -> Iterator[PartitionBounds]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pg_get_expr(child.relpartbound, child.oid) AS bound
                FROM pg_inherits
                JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
                JOIN pg_class child ON child.oid = pg_inherits.inhrelid
                WHERE parent.oid = %s::regclass
                ORDER BY bound;
                """,
                [table],
            )
            for (bound,) in cursor.fetchall():
                parsed = _parse_partition_bound(bound)
                if parsed:
                    yield parsed

    def _indexed_columns(self, connection) -> Iterator[str]:
        model = LogEntry
        for field in model._meta.local_fields:
            if field.primary_key:
                continue
            if getattr(field, "db_index", False) or field.unique:
                yield field.column
        for index in getattr(model._meta, "indexes", []):
            with contextlib.suppress(IndexError):
                yield index.fields[0]

    def _table_rowcount(self, connection, table: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {self._qn(connection, table)};")
            return cursor.fetchone()[0]

    def _table_max_id(self, connection, table: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COALESCE(MAX(id), 0) FROM {self._qn(connection, table)};"
            )
            return cursor.fetchone()[0] or 0

    def _timestamp_bounds(self, connection, table: str) -> PartitionBounds | None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT MIN(timestamp), MAX(timestamp) FROM {self._qn(connection, table)};"
            )
            result = cursor.fetchone()
        if not result or result[0] is None or result[1] is None:
            return None
        min_ts, max_ts = result
        # Ensure upper bound extends to cover the full month of the max timestamp.
        max_month = _month_start(max_ts.date())
        upper = _partition_bounds_for_month(max_month).upper
        return PartitionBounds(lower=result[0], upper=upper)

    def _sequence_name(self, connection, table: str) -> str | None:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_get_serial_sequence(%s, 'id');",
                [table],
            )
            row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return None

    def _target_sequence_name(self, sequence: str, table: str) -> str:
        schema, _ = _split_schema_name(sequence)
        base_table = _base_table_name(table)
        target = f"{base_table}_id_seq"
        return f"{schema}.{target}" if schema else target

    def _rename_sequence(self, connection, sequence: str, target: str) -> str:
        schema, _ = _split_schema_name(sequence)
        target_schema, target_name = _split_schema_name(target)
        if schema and target_schema and schema != target_schema:
            raise CommandError("Cannot move sequence across schemas.")
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER SEQUENCE {sequence} RENAME TO {name};".format(
                    sequence=self._qn(connection, sequence),
                    name=connection.ops.quote_name(target_name),
                )
            )
        final_schema = schema or target_schema
        return f"{final_schema}.{target_name}" if final_schema else target_name

    def _collect_partition_months(
        self,
        bounds: PartitionBounds | None,
        ahead: int | None,
        retention_months: int | None,
    ) -> list[datetime.date]:
        months: set[datetime.date] = set()
        today_month = _month_start(datetime.date.today())

        if bounds:
            min_month = _month_start(bounds.lower.date())
            max_month = _add_months(_month_start(bounds.upper.date()), -1)
            end_month = _add_months(max_month, 1)
            for month in _iter_months(min_month, end_month, inclusive=False):
                months.add(month)
        else:
            months.add(today_month)

        if retention_months and retention_months > 0:
            retention_start = _add_months(today_month, -retention_months)
            for month in _iter_months(retention_start, today_month, inclusive=False):
                months.add(month)

        ahead_value = max(ahead or 0, 0)
        for offset in range(ahead_value + 1):
            months.add(_add_months(today_month, offset))

        return sorted(months)

    def _copy_table_to_shadow(
        self,
        connection,
        source_table: str,
        target_table: str,
        partitions: Iterable[PartitionBounds],
        max_id_snapshot: int,
    ):
        for partition in partitions:
            params: list[object] = [partition.lower, partition.upper]
            query = (
                f"INSERT INTO {self._qn(connection, target_table)} "
                f"SELECT * FROM {self._qn(connection, source_table)} "
                f"WHERE timestamp >= %s AND timestamp < %s"
            )
            if max_id_snapshot > 0:
                query += " AND id <= %s"
                params.append(max_id_snapshot)
            with connection.cursor() as cursor:
                cursor.execute(query, params)

    def _sync_delta_rows(
        self,
        connection,
        source_table: str,
        target_table: str,
        last_copied_id: int,
    ):
        with connection.cursor() as cursor:
            if last_copied_id > 0:
                cursor.execute(
                    f"INSERT INTO {self._qn(connection, target_table)} "
                    f"SELECT * FROM {self._qn(connection, source_table)} "
                    f"WHERE id > %s;",
                    [last_copied_id],
                )
            else:
                cursor.execute(
                    f"INSERT INTO {self._qn(connection, target_table)} "
                    f"SELECT * FROM {self._qn(connection, source_table)};"
                )

    def _ensure_table_absent(self, connection, table: str):
        if self._table_exists(connection, table):
            raise CommandError(
                f"Temporary table '{table}' already exists. "
                "Drop or rename it before running init."
            )

    def _drop_table_if_exists(self, connection, table: str):
        if self._table_exists(connection, table):
            self._drop_table(connection, table)

    def _qn(self, connection, name: str, allow_schema: bool = True) -> str:
        if allow_schema and "." in name:
            schema, obj = name.split(".", 1)
            return (
                f"{connection.ops.quote_name(schema)}.{connection.ops.quote_name(obj)}"
            )
        return connection.ops.quote_name(name)


def _parse_year_month(value: str) -> datetime.date:
    try:
        year, month = map(int, value.split("-", 1))
        return datetime.date(year=year, month=month, day=1)
    except Exception as exc:  # pragma: no cover - arg parsing ensures int
        raise CommandError(f"Invalid YYYY-MM value '{value}'.") from exc


def _split_schema_name(qualified_name: str):
    if "." in qualified_name:
        schema, name = qualified_name.split(".", 1)
        return schema, name
    return None, qualified_name


def _base_table_name(table: str) -> str:
    return table.split(".", 1)[-1]


def _qualified_name(schema: str | None, name: str) -> str:
    return f"{schema}.{name}" if schema else name


def _coalesce_int(value: int | None, default: int | None) -> int | None:
    return value if value is not None else default


def _month_start(date_value: datetime.date) -> datetime.date:
    return date_value.replace(day=1)


def _add_months(date_value: datetime.date, months: int) -> datetime.date:
    year = date_value.year + (date_value.month - 1 + months) // 12
    month = (date_value.month - 1 + months) % 12 + 1
    return datetime.date(year, month, 1)


def _iter_months(
    start: datetime.date, end: datetime.date, *, inclusive: bool
) -> Iterator[datetime.date]:
    current = start
    while current < end if not inclusive else current <= end:
        yield current
        current = _add_months(current, 1)


def _partition_bounds_for_month(month: datetime.date) -> PartitionBounds:
    lower = datetime.datetime.combine(month, datetime.time.min).replace(
        tzinfo=datetime.timezone.utc
    )
    upper_month = _add_months(month, 1)
    upper = datetime.datetime.combine(upper_month, datetime.time.min).replace(
        tzinfo=datetime.timezone.utc
    )
    return PartitionBounds(lower=lower, upper=upper)


def _parse_partition_bound(bound: str) -> PartitionBounds | None:
    # Example: "FOR VALUES FROM ('2025-11-01 00:00:00+00') TO ('2025-12-01 00:00:00+00')"
    try:
        tokens = bound.replace("FOR VALUES FROM (", "").replace(")", "")
        lower_part, _, upper_part = tokens.partition(" TO ")
        lower_str = lower_part.strip(" '")
        upper_str = upper_part.strip(" '")
        lower_dt = datetime.datetime.fromisoformat(lower_str)
        upper_dt = datetime.datetime.fromisoformat(upper_str)
        return PartitionBounds(lower=lower_dt, upper=upper_dt)
    except Exception:
        return None
