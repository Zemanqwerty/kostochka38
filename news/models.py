# -*- coding: utf-8 -*-
from core.models import *
import datetime
from ckeditor.fields import RichTextField

STATUS = (
    ('1', u'На рассмотрении'),
    ('2', u'Опубликованная'),
    ('3', u'Отклоненная')
)

STATUS_ACTION = (
    ('1', u'В ожидании старта'),
    ('2', u'Действующая'),
    ('3', u'Прошедшая')
)

ACTION_TARGET = (
    (0, u'Везде'),
    (1, u'Онлайн'),
    (2, u'Розница')
)


class New(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата публикации')
    exp_date = models.DateTimeField(verbose_name=u'Дата завершения', null=True, blank=True)
    short = RichTextField(blank=True, null=True,
                          help_text=u"Короткая версия текста новости/статьи, будет отображаться в общем спике новостей.",
                          verbose_name=u'Короткая версия текста')
    social_short = models.CharField(blank=True, null=True, verbose_name=u'Короткий текст для соц. сетей',
                                    max_length=256)
    body = RichTextField(
        help_text=u"Полная версия текста новости/статьи, будет отображаться при детальном просмотре новости.",
        verbose_name=u'Полная версия текста')
    status = models.CharField(max_length=1, choices=STATUS, verbose_name=u'Статус', default='2')
    link = models.CharField(max_length=512)
    action = models.BooleanField(default=False, verbose_name=u'Акция')
    action_target = models.PositiveSmallIntegerField(verbose_name=u'Область применения', choices=ACTION_TARGET, default=0)
    complete = models.BooleanField(default=False, verbose_name=u'Акция завершена?')
    discount_size = models.FloatField(verbose_name=u'Размер скидки', null=True, blank=True)
    html_title = models.CharField(u"HTML Title", max_length=255, default=u"", blank=True)
    original_image = ProcessedImageField(upload_to=get_file_path,
                                         options={'qaulity': 80},
                                         processors=[ResizeToFit(1024, 768), ],
                                         verbose_name=u'фото')
    thumbnail = ImageSpecField(source='original_image', processors=[ResizeToFit(270, 200), ],
                               options={'quality': 80})

    meta_description = models.CharField("description", max_length=255, blank=True)
    meta_keywords = models.CharField("keywords", max_length=255, blank=True)

    seo_text = models.TextField(u"SEO текст", blank=True)
    directory_string_var = 'news_photo'

    order = models.PositiveIntegerField(verbose_name=u'Порядок', default=0)

    def photo(self):
        if self.original_image:
            try:
                return '<img height="100px" src="%s">' % self.thumbnail.url
            except IOError:
                return False
        else:
            return False

    photo.allow_tags = True
    photo.short_description = u'Фото'

    def get_comment_count(self):
        return Comment.objects.filter(new=self.id, status=2).count()

    def get_action_link(self):
        return '/promo/%s/' % self.link

    def __str__(self):
        return self.title

    def get_item(self):
        return NewItems.objects.filter(new_id=self.id)

    def get_absolute_url(self):
        return "/news/%s/" % self.link

    class Meta:
        ordering = ['-order', ]
        verbose_name = u"Новость/Акция"
        verbose_name_plural = u"Новости/Акции"

    def save(self, *args, **kwargs):
        if not self.link:
            trans_title = pytils.translit.slugify(self.title)
            date = datetime.datetime.now()
            self.link = trans_title + '_' + str(date.day) + '-' + str(date.month) + '-' + str(date.year)
        super(New, self).save(*args, **kwargs)


class NewItems(models.Model):
    new = models.ForeignKey(New, verbose_name=u'Акция', on_delete=models.CASCADE)
    item = models.ForeignKey('catalog.Item', verbose_name='Товар', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(verbose_name=u'Порядок', default=0)

    def get_thumbnail(self):
        return self.item.deckitem.photo_big_thumb()

    get_thumbnail.short_description = u'Фото'
    get_thumbnail.allow_tags = True

    def item__code(self):
        return self.item.article

    item__code.short_description = u'Код'

    # def buy_count_3_month(self):
    #     stop_date = datetime.datetime.now()
    #     start_date = stop_date - datetime.timedelta(days=90)
    #     counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item).aggregate(sum=Sum('quantity'))['sum']
    #     if counts is None:
    #         counts = format_html("[<span style='color:#b26'>{0} шт</span>]", 0)
    #     else:
    #         counts = format_html("[<span style='color:#2b6'><b>{0}</b> шт</span>]", counts)
    #     return counts
    # buy_count_3_month.allow_tags = True
    # buy_count_3_month.short_description = u'Куплено за 3 месяца'

    class Meta:
        ordering = ['order']
        verbose_name = u"товар в акции"
        verbose_name_plural = u"товар в акции"


class Vopros_otvet(models.Model):
    date = models.DateTimeField(verbose_name=u'Дата публикации', help_text="используется для сортировки", )
    vopros = models.CharField(max_length=512, verbose_name=u'Вопрос')
    otvet = models.TextField(blank=True, null=True, verbose_name=u'Ответ')

    class Meta:
        verbose_name = u"Совет ветеринара"
        verbose_name_plural = u"Советы ветеринара"


class Comment(models.Model):
    owner = models.ForeignKey(Account, blank=True, null=True, on_delete=models.CASCADE)
    author = models.CharField(max_length=128, blank=True, null=True)
    new = models.ForeignKey(New, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    body = RichTextField()
    status = models.CharField(max_length=1, choices=STATUS)

    def __str__(self):
        return self.body

    class Meta:
        verbose_name = u"Комментарий к новости"
        verbose_name_plural = u"Комментарии к новостям"
