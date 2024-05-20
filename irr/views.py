# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
from xml.etree.ElementTree import Element, SubElement, Comment, ProcessingInstruction, _escape_cdata, \
    _escape_attrib, QName
import xml.etree.ElementTree as ElementTree
from catalog.models import Deckitem
from django.conf import settings
from django.http.response import HttpResponse
from django.utils.html import strip_tags
import hashlib


def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

DOMAIN = u'http://kostochka38.ru'


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


def create_xml(request):
    users = Element(u'users')
    user = SubElement(users, u'user', {u'deactivate-untouched': u'false'})
    match = SubElement(user, u'match')
    user_id = SubElement(match, u'user-id')
    user_id.text = u'15844309'
    now = datetime.now()
    later = now + timedelta(hours=25)
    for deck_item in Deckitem.objects.filter(active=1).select_related('producer').all():
        for item in deck_item.items().all():
            category = u'/animals-plants/accessories/food/'
            other = False
            # if deck_item.tags.exclude(product=0).exists():
            #     other = True
            #     category = '/animals-plants/accessories/other/'
            fmt = '%Y-%m-%dT%H:%M:%S'
            store_ad = SubElement(user, u'store-ad', {
                u'category': category,
                u'power-ad': u'1',
                u'source-id': u'{}'.format(item.id),
                u'validfrom': now.strftime(fmt),
                u'validtill': later.strftime(fmt),
            })
            title = SubElement(store_ad, u'title')
            title.text = u'{}, {}, {}'.format(deck_item.producer.title, deck_item.title, item.weight)
            description = SubElement(store_ad, u'description')
            description.text = strip_tags(deck_item.description if deck_item.description else deck_item.title)
            SubElement(store_ad, u'price', {
                u'value': u'{}'.format(item.current_price()),
                u'currency': u'RUR'
            })

            fotos = SubElement(store_ad, u'fotos')

            if item.deckitem.cover():
                image_url =item.deckitem.cover()[0].original_image.url
            else:
                image_url = 'http://kostochka38.ru/staticfiles/images/noimage.png'
            foto = SubElement(fotos, u'foto-remote', {
                u'url': u'{}{}'.format(DOMAIN, image_url),
            })

            if item.deckitem.cover():
                try:
                    foto.set(u'md5', hashfile(item.deckitem.cover()[0].original_image.file, hashlib.md5())),
                except IOError:
                    pass

            custom_fields = SubElement(store_ad, u'custom-fields')
            field = SubElement(custom_fields, u'field', {u'name': u'offertype'})
            field.text = u'продам'
            # if other:
            #     field = SubElement(custom_fields, u'field', {u'name': u'used-or-new'})
            #     field.text = u'новый'
            # else:
            #     field = SubElement(custom_fields, u'field', {u'name': u'type'})
                # field.text = u'другие'
                # if deck_item.tags.filter(section='1').exists():
                #     field.text = u'собаки'
                # elif deck_item.tags.filter(section='2').exists():
                #     field.text = u'кошки'
            field = SubElement(custom_fields, u'field', {u'name': u'region'})
            field.text = u'Иркутская'
            field = SubElement(custom_fields, u'field', {u'name': u'address_city'})
            field.text = u'Иркутск'
            # field = SubElement(custom_fields, u'field', {u'name': u'address_street'})
            # field.text = u'Иркутск'
            # field = SubElement(custom_fields, u'field', {u'name': u'address_house'})
            # field.text = u'Иркутск'
            field = SubElement(custom_fields, u'field', {u'name': u'web'})
            field.text = u'{}{}?utm_medium=price&utm_source=irr'.format(DOMAIN, deck_item.get_absolute_url())
            if hasattr(settings, 'IRR_EMAIL'):
                field = SubElement(custom_fields, u'field', {u'name': u'email'})
                field.text = settings.IRR_EMAIL
            if hasattr(settings, 'IRR_PHONE'):
                field = SubElement(custom_fields, u'field', {u'name': u'phone'})
                field.text = settings.IRR_PHONE
            if hasattr(settings, 'IRR_CONTACT'):
                field = SubElement(custom_fields, u'field', {u'name': u'contact'})
                field.text = settings.IRR_CONTACT
    file = open(os.path.join(settings.MEDIA_ROOT, 'export.xml'), 'wb')
    file.write('<?xml version="1.0" encoding="utf-8"?>\n{}'.format(ElementTree.tostring(users, encoding='utf-8')))
    file.close()
    return HttpResponse()
