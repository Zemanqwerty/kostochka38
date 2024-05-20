# -*- coding: utf-8 -*-

import itertools

from pytils.translit import slugify

from django.core.management import BaseCommand
from django.utils.decorators import method_decorator
from django.db.models import Q

from catalog.models import Tag, FilterSitemapLink, Filter, Deckitem, Producer
from catalog.tuples import SECTION_DICT


class Command(BaseCommand):

    def handle(self, *args, **options):
        FilterSitemapLink.objects.all().delete()
        id = 0
        for tag in Tag.objects.filter(link__in=['korm-dlya-sobak', 'korm-dlya-koshek']):
            f_list, producers_count = get_f_list(tag.groupfilter_set.exclude(link='other'))
            for combination, keywords, producer, filters in get_f_list_links(f_list, tag.groupfilter_set.exclude(link='other').count() + producers_count):
                if deckitems_exists(combination, tag):
                    grammar = get_grammar(tag, combination)
                    sentence = generate_sentence(grammar)
                    slug = slugify(sentence)
                    section_title = SECTION_DICT.get(tag.section)
                    link = FilterSitemapLink.objects.create(
                        id=id,
                        title=sentence,
                        keywords=keywords,
                        slug=slug,
                        producer=producer
                    )
                    for f in filters:
                        link.filters.add(f)
                    id += 1
        print(u'Ссылок создано: %s' % FilterSitemapLink.objects.count())


def get_f_list(gf_queryset):
    f_list = []
    for gf in gf_queryset:
        f_list.extend(gf.filter.all())

    ids = [f.id for f in f_list]
    producers = Producer.objects.filter(deckitem__filter__id__in=ids).distinct()
    f_list.extend(producers)

    return f_list, producers.count()


def combination_is_invalid(combination):
    '''
    Возвращает "False", если в сочетании встречается более одного
    производителя, либо более одного фильтра из одной группы
    '''
    groupfilters = [f.groupfilter_set.first() for f in combination if isinstance(f, Filter)]
    producers = [p for p in combination if isinstance(p, Producer)]
    if len(producers) > 1:
        return True
    else:
        for gf in groupfilters:
            if groupfilters.count(gf) > 1:
                return True
    return False


def get_f_list_links(f_list, gf_count):
    for r in range(1, gf_count + 1):
        for combination in itertools.combinations(f_list, r):
            if not combination_is_invalid(combination):
                producer = None
                for f in combination:
                    if isinstance(f, Producer):
                        producer = f
                        break
                filters = [f for f in combination if isinstance(f, Filter)]

                class_filter_exists = False
                for f in filters:
                    if f.groupfilter_set.first().title == u'Класс':
                        class_filter_exists = True
                        break

                if class_filter_exists:
                    keywords = ' '.join([f.seo_title or f.title for f in filters]).replace(', ', '')
                else:
                    keywords = ' '.join([f.seo_title or f.title for f in filters] + [u'корм']).replace(', ', '')

                if producer is not None:
                    keywords += ' ' + producer.title
                yield combination, keywords, producer, filters


def deckitems_exists(filters, tag):
    producer = None
    for f in filters:
        if isinstance(f, Producer):
            producer = f
            break
    filters = [f for f in filters if isinstance(f, Filter)]

    query = tag.deckitems.filter(active=True)
    
    for f in filters:
        filters_item = f.deckitems.filter(active=1).values_list('id', flat=True).distinct()
        query = query.filter(id__in=filters_item).distinct()

    if producer is not None:
        query = query.filter(producer=producer)

    return query.count() > 0


def is_terminal(token):
    return token[0] != '_'


def expand(grammar, tokens):
    for i, token in enumerate(tokens):
        if token == '' or is_terminal(token):
            continue
        replacement = grammar[token][0]
        if replacement is None:
            tokens[i] = ''
        elif is_terminal(replacement):
            tokens[i] = replacement
        else:
            tokens = tokens[:i] + replacement.split() + tokens[(i+1):]
        return expand(grammar, tokens)
    return tokens


def generate_sentence(grammar):
    return ' '.join(expand(grammar, ['_S'])).replace(' blank', '').replace(' ,', ',')


def get_grammar(tag, filters):

    producer = None
    for f in filters:
        if isinstance(f, Producer):
            producer = f
            break

    ids = [f.id for f in filters if isinstance(f, Filter)]
    filters = Filter.objects.filter(id__in=ids)

    if tag.link == 'korm-dlya-sobak':
        f_type = filters.filter(groupfilter__link='type').first()
        f_class = filters.filter(groupfilter__link='class').first()
        f_size = filters.filter(groupfilter__link='size').first()
        f_age = filters.filter(groupfilter__link='age').first()
        f_breed = filters.filter(groupfilter__link='poroda-dog').first()
        f_taste = filters.filter(groupfilter__link='vkus-dog').first()
        f_package = filters.filter(groupfilter__link='upakovka-dog').first()

        '''
        Купить 
        [сухой/влажный/...] 
        [премиум корм/эконом корм....] / корм
        [royal cacnin/hills....] 
        для 
        [маленких/крупных/средних] 
        [врзрослых собак/пожилых собак/щенков]  / собак
        [породы мопс/лабрадор....] 
        [вкус Курица/овощи/говядина...]
        [, консерва/пауч...] 
        в Иркутске
        '''

        return {
            '_S': ['_ACT _TYPE _CLASS _PROD _FOR _SIZE _AGE _BREED _TASTE _PACKAGE _PLACE'],
            '_ACT': [u'Купить'],
            '_TYPE': [f_type.seo_title or f_type.title if f_type else 'blank'],
            '_CLASS': [f_class.seo_title or f_class.title if f_class else u'корм'],
            '_PROD': [producer.title if producer else 'blank'],
            '_FOR': [u'для'],
            '_SIZE': [f_size.seo_title or f_size.title if f_size else 'blank'],
            '_AGE': [f_age.seo_title or f_age.title if f_age else u'собак'],
            '_BREED': [f_breed.seo_title or f_breed.title if f_breed else 'blank'],
            '_TASTE': [f_taste.seo_title or f_taste.title if f_taste else 'blank'],
            '_PACKAGE': [f_package.seo_title or f_package.title if f_package else 'blank'],
            '_PLACE': [u'в Иркутске'],
        }

    elif tag.link == 'korm-dlya-koshek':
        f_type = filters.filter(groupfilter__link='type').first()
        f_class = filters.filter(groupfilter__link='class').first()
        f_age = filters.filter(groupfilter__link='age').first()
        f_breed = filters.filter(groupfilter__link='poroda-cat').first()
        f_taste = filters.filter(groupfilter__link='vkus').first()
        f_package = filters.filter(groupfilter__link='upakovka').first()

        '''
        Купить 
        [сухой/влажный/...] 
        [премиум корм/эконом корм...] / корм
        [royal cacnin/hills....] 
        для  
        [врзрослых кошек/пожилых кошек/котят] / кошек  
        [породы мейнк кун/породы сибирская....] 
        [вкус Курица/овощи/говядина...]
        [, консерва/пауч...] 
        в Иркутске
        '''

        return {
            '_S': ['_ACT _TYPE _CLASS _PROD _FOR _AGE _BREED _TASTE _PACKAGE _PLACE'],
            '_ACT': [u'Купить'],
            '_TYPE': [f_type.seo_title or f_type.title if f_type else 'blank'],
            '_CLASS': [f_class.seo_title or f_class.title if f_class else u'корм'],
            '_PROD': [producer.title if producer else 'blank'],
            '_FOR': [u'для'],
            '_AGE': [f_age.seo_title or f_age.title if f_age else u'кошек'],
            '_BREED': [f_breed.seo_title or f_breed.title if f_breed else 'blank'],
            '_TASTE': [f_taste.seo_title or f_taste.title if f_taste else 'blank'],
            '_PACKAGE': [f_package.seo_title or f_package.title if f_package else 'blank'],
            '_PLACE': [u'в Иркутске'],
        }

    return {
        '_S': ['Косточка']
    }