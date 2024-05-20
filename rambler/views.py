# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
from xml.etree.ElementTree import Element, SubElement, Comment, ProcessingInstruction, _escape_cdata, \
    _escape_attrib, QName
import xml.etree.ElementTree as ElementTree
from catalog.models import Deckitem, Tag
from django.conf import settings
from django.http.response import HttpResponse
from django.utils.html import strip_tags
import hashlib
from catalog.tuples import SECTION_DICT

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

DOMAIN = u'https://kostochka38.ru'

#
def _serialize_xml(write, elem, encoding, qnames, namespaces):
    tag = elem.tag
    text = elem.text
    if tag is Comment:
        write("<!--%s-->" % text)
    elif tag is ProcessingInstruction:
        write("<?%s?>" % text)
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(_escape_cdata(text, encoding))
            for e in elem:
                _serialize_xml(write, e, encoding, qnames, None)
        else:
            write("<" + tag)
            items = elem.items()
            if items or namespaces:
                if namespaces:
                    for v, k in sorted(namespaces.items(),
                                       key=lambda x: x[1]):  # sort on prefix
                        if k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k.encode(encoding),
                            _escape_attrib(v, encoding)
                            ))
                for k, v in items:  # lexical order
                    if isinstance(k, QName):
                        k = k.text
                    if isinstance(v, QName):
                        v = qnames[v.text]
                    else:
                        v = _escape_attrib(v, encoding)
                    write(" %s=\"%s\"" % (qnames[k], v))
            if text or len(elem):
                write(">")
                if text:
                    write(_escape_cdata(text, encoding))
                for e in elem:
                    _serialize_xml(write, e, encoding, qnames, None)
                write("</" + tag + ">")
            else:
                write(" />")
    if elem.tail:
        write(_escape_cdata(elem.tail, encoding))

ElementTree._serialize['xml'] = _serialize_xml


def create_yml(request):
    fmt = '%Y-%m-%d %H:%M'

    now = datetime.now()
    yml_catalog = Element(u'yml_catalog', {u'date': now.strftime(fmt)})

    shop = SubElement(yml_catalog, u'shop')

    name = SubElement(shop, u'name')
    name.text = u'Kostochka38'
    company = SubElement(shop, u'company')
    company.text = u'ООО Косточка38'
    url = SubElement(shop, u'url')
    url.text = u'https://kostochka38.ru'

    currencies = SubElement(shop, u'currencies')
    currency = SubElement(currencies, u'currency', {u'id': u'RUR', u'rate': u'1'})

    categories = SubElement(shop, u'categories')
    for category in Tag.objects.all().values():
        category_element = SubElement(categories, u'category', {u'id': str(category['id'])})
        category_element.text = u'%s %s' % (category['title'], SECTION_DICT[category['section']])

    delivery_options = SubElement(shop, u'delivery-options')
    option = SubElement(delivery_options, u'option', {u'cost': u'150', u'days': u'0', u'order-before': u'12'})
    option = SubElement(delivery_options, u'option', {u'cost': u'150', u'days': u'1', u'order-before': u'24'})

    offers = SubElement(shop, u'offers')

    n = 0
    for deck_item in Deckitem.objects.filter(active=1).select_related('producer').all():
        for item in deck_item.items().filter(active=1).exclude(availability=0):
            offer = SubElement(offers, u'offer', {u'id': str(item.id)})

            url = SubElement(offer, u'url')
            url.text = u'https://kostochka38.ru/c/i/%s/' % item.deckitem.link
            price = SubElement(offer, u'price')
            price.text = str(item.current_price())
            currencyId = SubElement(offer, u'currencyId')
            currencyId.text = u'RUR'
            categoryId = SubElement(offer, u'categoryId')
            categoryId.text = str(item.deckitem.tag.id)
            name = SubElement(offer, u'name')
            name.text =  item.deckitem.title.replace('"', '&quot;').replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", '&apos;')
            vendor = SubElement(offer, u'vendor')
            vendor.text = item.deckitem.producer.title.replace('"', '&quot;').replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", '&apos;')
            model = SubElement(offer, u'model')
            model.text = item.weight.replace('"', '&quot;').replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", '&apos;')
            if item.deckitem.title_en:
                description = SubElement(offer, u'description')
                description.text = item.deckitem.title_en.replace('"', '&quot;').replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", '&apos;')

            for photo in item.deckitem.photos():
                picture = SubElement(offer, u'picture')
                picture.text = u'https://kostochka38.ru%s' % photo.fullimage.url

            n += 1

    yml_file = open(os.path.join(settings.MEDIA_ROOT, 'export.xml'), 'wb')
    yml_file.write('<?xml version="1.0" encoding="utf-8"?>\n{}'.format(ElementTree.tostring(yml_catalog, encoding='utf-8')))
    yml_file.close()
    return HttpResponse()






















