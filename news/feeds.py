from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from news.models import *

class LatestNews(Feed):
    title = u"Последние новости"
    link = u"/news/"
    description = u"все рубрики"

    def items(self):
        return New.objects.order_by('-date')[:5]

class LatestNewsByCategory(Feed):
    def get_object(self, category):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such
        # clutter, check that bits has only one member.
        if len(category) != 1:
            raise ObjectDoesNotExist
        return Tag.objects.get(link=category[0])

    def title(self, obj):
        return u'Последние новости. Рубрика "%s".' % obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return u"описание %s" % obj.title

    def items(self, obj):
        news =  news = obj.new_set.all()
        return news.order_by('-date')[:5]
