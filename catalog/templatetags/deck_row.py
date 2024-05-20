# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.simple_tag
def calc_height(item_id, height, items_per_row):
    if item_id % items_per_row == 0:
        return '{}'.format(item_id / items_per_row * height)
    else:
        return '{}'.format((item_id / items_per_row + 1) * height)

@register.simple_tag
def calc_width(item_id, width, items_per_row):
    return '{}'.format(item_id % items_per_row * width)


@register.inclusion_tag('card_title.html')
def get_title(item):
    if not isinstance(item, dict):
        title = u'{}, {}'.format(item.producer, item.title)
    else:
        title = u'{}, {}'.format(item['producer'], item['title'])
    card_title_head = u''
    card_title_tail = u''
    line_number = 1
    max_line = 3
    line_length_base = 28
    line_length = line_length_base
    title_head_length = 82
    line = u''
    title_array = title.split()
    i = 0
    while i < len(title_array):
        word = title_array[i]
        if line_number > max_line:
            card_title_tail = u' '.join([card_title_tail, word]).strip()
            i += 1
            continue
        if ((line_number < max_line and len(u' '.join([line, word])) < line_length)
                or (line_number == max_line and len(u' '.join([line, word])) < line_length - (0 if i == len(title_array) - 1 else 4)
                    and len(u' '.join([card_title_head, line, word])) < title_head_length)
            ):
            line = u' '.join([line, word]).strip()
            if len(line.split()) > 2 and line_length < 30:
                line_length += 1
            i += 1
            if i == len(title_array):
                card_title_head = u' '.join([card_title_head, line]).strip()
        else:
            card_title_head = u' '.join([card_title_head, line]).strip()
            line = u''
            line_number += 1
            line_length = line_length_base
    return {
        'card_title_head': card_title_head,
        'card_title_tail': card_title_tail,
    }