# -*- coding: utf-8 -*-
#
u""" Catalog widgets. """

from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms import CheckboxSelectMultiple as DjangoCheckboxSelectMultiple, CheckboxInput
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CheckboxSelectMultiple(DjangoCheckboxSelectMultiple):

    u""" CheckboxSelectMultiple. """

    COLUMNS = 3

    def render(self, name, value, attrs=None, choices=()):
        u""" Render choice field. """
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        # Normalize to strings
        str_values = set([force_str(v) for v in value])
        # options = list(self.choices)
        tags = {}

        for item in self.choices.queryset.filter(parent__isnull=True):
            for group in item.groupfilter_set.all():
                if group not in tags:
                    tags[group] = []
                if item not in tags[group]:
                    tags[group].append(item)
                for sitem in item.filter_set.all():
                    if sitem not in tags[group]:
                        tags[group].append(sitem)
        output = []

        output.append('<div style="clear:both;margin:10px;">')
        i = 0
        for tag, options in tags.items():
            output.append('<ul style="float:left;list-style:none;padding-left: 0; border: 1px solid #eee; border-radius: 5px; padding-right: 0px; margin-right: 5px !important;">')
            output.append('<li style="list-style:none;"><h3>%s<br><small style="text-transform: lowercase;">(%s)</small></h3></li>' % (tag.title, tag.tag.get_section_display()))
            options = list(options)
            for option in options:
                # If an ID attribute was given, add a numeric index as a suffix,
                # so that the checkboxes don't all have the same ID attribute.
                if has_id:
                    final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                    label_for = format_html(' for="{0}"', final_attrs['id'])
                else:
                    label_for = ''

                cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
                # is_child = bool(option.parent)
                option_value = force_str(option.id)
                rendered_cb = cb.render(name, option_value)
                option_label = force_str(option.title)

                # if is_child:
                #     output.append(format_html(u'<li style="list-style:none; margin-left: 7px;"><label{0}>-- {1} {2}</label></li>',
                #                               label_for, rendered_cb, option_label))
                # else:
                output.append(format_html(u'<li style="list-style:none; margin-left: 7px;"><label{0}>{1} {2}</label></li>', label_for, rendered_cb, option_label))
                i += 1
            output.append('</ul>')
        output.append('<div style="clear:both"></div></div>')
        return mark_safe('\n'.join(output))


class InlineItemPhotoForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    def __init__(self, rel, admin_site, deckitem_id, attrs=None, using=None):
        self.deckitem_id = deckitem_id
        super(InlineItemPhotoForeignKeyRawIdWidget, self).__init__(rel, admin_site, attrs=attrs, using=using)

    def url_parameters(self):
        params = super(InlineItemPhotoForeignKeyRawIdWidget, self).url_parameters()
        if self.deckitem_id is not None:
            params['deckitem_id'] = self.deckitem_id
        return params