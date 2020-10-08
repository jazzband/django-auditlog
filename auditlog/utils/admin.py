from django.forms.utils import pretty_name
from django.urls import reverse
from django.utils.html import format_html


def get_headers(fields):
    for field in fields:
        yield {
            'text': pretty_name(field),
            'class_attrib': format_html(' class="column-{}"', field),
            'sortable': False,
        }


def items_for_result(result, fields, opts):
    first = True
    for field in fields:

        value = getattr(result, field)

        if first:
            first = False
            url = reverse(
                'admin:%s_%s_change' % (opts.app_label, opts.model_name),
                args=(result.id,),
                # current_app=self.model_admin.admin_site.name
            )
            link_or_text = format_html(
                '<a href="{}">{}</a>',
                url,
                value
            )
            yield format_html('<th>{}</th>', link_or_text)
        else:
            yield format_html('<td>{}</td>', value)


def results(result_list, fields, opts):
    for result in result_list:
        yield items_for_result(result, fields, opts)
