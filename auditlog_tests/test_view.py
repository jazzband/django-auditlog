from unittest.mock import patch

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from test_app.models import SimpleModel

from auditlog.mixins import AuditlogHistoryAdminMixin


class TestModelAdmin(AuditlogHistoryAdminMixin, admin.ModelAdmin):
    model = SimpleModel
    auditlog_history_per_page = 5


class TestAuditlogHistoryAdminMixin(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test_admin", is_staff=True, is_superuser=True, is_active=True
        )
        self.site = AdminSite()

        self.admin = TestModelAdmin(SimpleModel, self.site)

        self.obj = SimpleModel.objects.create(text="Test object")

    def test_auditlog_history_view_requires_permission(self):
        request = RequestFactory().get("/")
        request.user = get_user_model().objects.create_user(
            username="non_staff_user", password="testpass"
        )

        with self.assertRaises(Exception):
            self.admin.auditlog_history_view(request, str(self.obj.pk))

    def test_auditlog_history_view_with_permission(self):
        request = RequestFactory().get("/")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        self.assertEqual(response.status_code, 200)
        self.assertIn("log_entries", response.context_data)
        self.assertIn("object", response.context_data)
        self.assertEqual(response.context_data["object"], self.obj)

    def test_auditlog_history_view_pagination(self):
        """Test that pagination works correctly."""
        for i in range(10):
            self.obj.text = f"Updated text {i}"
            self.obj.save()

        request = RequestFactory().get("/")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        self.assertTrue(response.context_data["pagination_required"])
        self.assertEqual(len(response.context_data["log_entries"]), 5)

    def test_auditlog_history_view_page_parameter(self):
        # Create more log entries by updating the object
        for i in range(10):
            self.obj.text = f"Updated text {i}"
            self.obj.save()

        request = RequestFactory().get("/?p=2")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        # Should be on page 2
        self.assertEqual(response.context_data["log_entries"].number, 2)

    def test_auditlog_history_view_context_data(self):
        request = RequestFactory().get("/")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        context = response.context_data
        required_keys = [
            "title",
            "module_name",
            "page_range",
            "page_var",
            "pagination_required",
            "object",
            "opts",
            "log_entries",
        ]

        for key in required_keys:
            self.assertIn(key, context)

        self.assertIn(str(self.obj), context["title"])
        self.assertEqual(context["object"], self.obj)
        self.assertEqual(context["opts"], self.obj._meta)

    def test_auditlog_history_view_extra_context(self):
        request = RequestFactory().get("/")
        request.user = self.user

        extra_context = {"extra_key": "extra_value"}
        response = self.admin.auditlog_history_view(
            request, str(self.obj.pk), extra_context
        )

        self.assertIn("extra_key", response.context_data)
        self.assertEqual(response.context_data["extra_key"], "extra_value")

    def test_auditlog_history_view_template(self):
        request = RequestFactory().get("/")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        self.assertEqual(response.template_name, self.admin.auditlog_history_template)

    def test_auditlog_history_view_log_entries_ordering(self):
        self.obj.text = "First update"
        self.obj.save()
        self.obj.text = "Second update"
        self.obj.save()

        request = RequestFactory().get("/")
        request.user = self.user

        response = self.admin.auditlog_history_view(request, str(self.obj.pk))

        log_entries = list(response.context_data["log_entries"])
        self.assertGreaterEqual(log_entries[0].timestamp, log_entries[1].timestamp)

    def test_get_list_display_with_auditlog_link(self):
        self.admin.show_auditlog_history_link = True
        list_display = self.admin.get_list_display(RequestFactory().get("/"))

        self.assertIn("auditlog_link", list_display)

        self.admin.show_auditlog_history_link = False
        list_display = self.admin.get_list_display(RequestFactory().get("/"))

        self.assertNotIn("auditlog_link", list_display)

    def test_get_urls_includes_auditlog_url(self):
        urls = self.admin.get_urls()

        self.assertGreater(len(urls), 0)

        url_names = [
            url.name for url in urls if hasattr(url, "name") and url.name is not None
        ]
        auditlog_urls = [name for name in url_names if "auditlog" in name]
        self.assertGreater(len(auditlog_urls), 0)

    @patch("auditlog.mixins.reverse")
    def test_auditlog_link(self, mock_reverse):
        """Test that auditlog_link method returns correct HTML link."""
        # Mock the reverse function to return a test URL
        expected_url = f"/admin/test_app/simplemodel/{self.obj.pk}/auditlog/"
        mock_reverse.return_value = expected_url

        link_html = self.admin.auditlog_link(self.obj)

        self.assertIsInstance(link_html, str)

        self.assertIn("<a href=", link_html)
        self.assertIn("View</a>", link_html)

        self.assertIn(expected_url, link_html)

        opts = self.obj._meta
        expected_url_name = f"admin:{opts.app_label}_{opts.model_name}_auditlog"
        mock_reverse.assert_called_once_with(expected_url_name, args=[self.obj.pk])
