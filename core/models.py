# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import hashlib
import os
import random
import uuid
from campaign import models as campaign_models
import re
from django.conf import settings
from django import forms
from django.utils.encoding import force_str
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum, Count
from django.utils.html import format_html
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFit
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from catalog.tuples import *
from catalog.utils import is_digit

import pytils
import catalog

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(instance.directory_string_var, filename)


def intspace(value):
    orig = force_str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1> \g<2>', orig)
    if orig == new:
        return new
    else:
        return intspace(new)

# class Unsubscribed(models.Model):
#     subscriberlist = models.ForeignKey(campaign_models.SubscriberList)
#     user = models.ForeignKey('Account', related_name='unsubscribe_items')


class UserSource(models.Model):
    title = models.CharField(verbose_name=u'Название', max_length=256)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def get_user_count(self):
        return Account.objects.filter(usersource=self.id).aggregate(count=Count('id'))['count']

    class Meta:
        verbose_name = u"Источник узнавания"
        verbose_name_plural = u"Источники узнавания"


class Account(AbstractUser):
    usersource = models.ForeignKey(UserSource, verbose_name=u'Источник', default=1, on_delete=models.SET_DEFAULT)

    sale = models.FloatField(max_length=512, choices=SALE_GROUP, help_text=u"скидка 10% = 0.9", verbose_name=u'Скидка', blank=True, null=True)
    phone = models.CharField(max_length=32, verbose_name=u'Телефон', blank=True, null=True)

    customer = models.BooleanField(default=False, verbose_name=u'Покупатель')
    repeat_customer = models.BooleanField(default=False, verbose_name=u'Повторный покупатель')

    free_shipping = models.BooleanField(u'Бесплатная доставка', default=False)
    free_buyer = models.BooleanField(u'Покупать по себестоимости', default=False)

    unsubscribed = models.BooleanField(u'Отписан от рассылки', default=False)

    description = RichTextUploadingField(u'Комментарии', blank=True, null=True)

    ur_lico = models.BooleanField(verbose_name=u'Юридическое лицо', default=False)
    basket_of_goods = models.BooleanField(verbose_name=u'скрыть Корзину добра', default=False)
    zavodchik = models.BooleanField(verbose_name=u'Заводчик/питомник', default=False)
    optovik = models.BooleanField(verbose_name=u'Оптовик', default=False)

    name_pol = models.CharField(verbose_name=u'Наименование Грузополучателя', max_length=512, blank=True, null=True)
    inn_pol = models.BigIntegerField(verbose_name=u'ИНН Грузополучателя', blank=True, null=True)
    kpp_pol = models.BigIntegerField(verbose_name=u'КПП Грузополучателя', blank=True, null=True)
    address_pol = models.CharField(verbose_name=u'Адрес Грузополучателя', max_length=512, blank=True, null=True)
    okpo_pol = models.IntegerField(verbose_name=u'ОКПО Грузополучателя', blank=True, null=True)

    name_plat = models.CharField(verbose_name=u'Наименование Плательщика', max_length=512, blank=True, null=True)
    inn_plat = models.BigIntegerField(verbose_name=u'ИНН Плательщика', blank=True, null=True)
    kpp_plat = models.BigIntegerField(verbose_name=u'КПП Плательщика', blank=True, null=True)
    address_plat = models.CharField(verbose_name=u'Адрес Плательщика', max_length=512, blank=True, null=True)
    okpo_plat = models.IntegerField(verbose_name=u'ОКПО Плательщика', blank=True, null=True)

    is_employed = models.BooleanField(verbose_name=u'Трудоустроен', default=False)
    name_cashier = models.CharField(verbose_name=u'Наименование Кассира', max_length=512, blank=True, null=True)
    inn_cashier = models.CharField(verbose_name=u'ИНН Кассира', blank=True, null=True, max_length=32)

    order_sum = models.IntegerField(verbose_name=u'Сумма заказов', blank=True, null=True)

    def get_humanize_sale(self):
        if self.sale:
            sale = (1 - self.sale) * 100
            sale = round(sale)
            return sale
        else:
            return 0

    def get_summ_zakaz(self):
        summ = catalog.models.Zakaz.objects.filter(status=6, owner=self.id).aggregate(summ=Sum('summ'))['summ']
        return str(intspace(summ)) + u' руб.'
    get_summ_zakaz.short_description = u'Сумма заказов'
    get_summ_zakaz.admin_order_field = 'order_sum'

    def save(self, *args, **kwargs):
        new_phone = ""
        for char in str(self.phone):
            if is_digit(char):
                new_phone += char
        self.phone = new_phone
        super(AbstractUser, self).save(*args, **kwargs)


    def __str__(self):
        if self.last_name:
            return '%s %s (%s)' % (self.first_name, self.last_name, self.username)
        else:
            return '%s (%s)' % (self.first_name, self.username)


from django.contrib.auth.forms import UserChangeForm, UserCreationForm
class AccountChangeForm(UserChangeForm):
    class Meta:
        fields = []
        model = Account


class AccountCreationForm(UserCreationForm):
    class Meta:
        fields = []
        model = Account

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            self._meta.model._default_manager.get(username=username)
        except self._meta.model.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])


class LostUser(models.Model):
    user = models.ForeignKey(Account, verbose_name=u'Покупатель', on_delete=models.CASCADE)
    create_date = models.DateTimeField(verbose_name=u'Дата занесения', auto_now_add=True)

    need_again = models.BooleanField(verbose_name=u'Обработать повторно', default=False)

    order_count = models.PositiveIntegerField(verbose_name=u'Количество заказов')
    average = models.PositiveIntegerField(verbose_name=u'Среднее')
    mediana = models.PositiveIntegerField(verbose_name=u'Медиана')
    last_order = models.PositiveIntegerField(verbose_name=u'Последний заказ')

    status = models.IntegerField(default=1, verbose_name=u'Статус', choices=LOST_USER_STATUS)
    description = models.TextField(verbose_name=u'Комментарий', blank=True)

    def __str__(self):
        return str(self.user.id)

    def go_to_user(self):
        return format_html(u'<a href="/DgJrfdJg/core/account/{0}/change/">User &rarr;</a>', self.user.id)
    go_to_user.allow_tags = True
    go_to_user.short_description = u'Юзер'

    class Meta:
        verbose_name = u"Потерянные покупатели"
        verbose_name_plural = u"Потерянные покупатели"


class Static(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    body = RichTextField(verbose_name=u'Текст страницы')
    link = models.CharField(max_length=512, verbose_name=u'URL адрес страницы', help_text=u'Это поле заполняется Оптимизатором сайта, и может быть оставлено пустым.', blank=True, null=True)
    menu = models.CharField(max_length=1, verbose_name=u'Расположение раздела', choices=MENU, default=1)
    active = models.BooleanField(default=1, verbose_name=u'Активная страница')
    number = models.IntegerField(default=19, verbose_name=u'Позиция в меню', help_text=u'Первым в меню будет тот раздел, чей номер меньше.')

    meta_title = models.CharField(max_length=1024, verbose_name=u'Мета title', help_text=u'Это поле заполняется Оптимизатором сайта, и может быть оставлено пустым.', blank=True, null=True)
    meta_descroption = models.CharField(max_length=1024, verbose_name=u'Мета descroption', help_text=u'Это поле заполняется Оптимизатором сайта, и может быть оставлено пустым.', blank=True, null=True)
    meta_keywords = models.CharField(max_length=1024, verbose_name=u'Мета keywords', help_text=u'Это поле заполняется Оптимизатором сайта, и может быть оставлено пустым.', blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return "/%i/" % self.link

    class Meta:
        verbose_name = u"Статический раздел"
        verbose_name_plural = u"Статические разделы"

    # def save(self):
    #     if not self.id and not self.link:
    #         link = pytils.translit.slugify(self.title)
    #
    #         if Static.objects.filter(link=link):
    #             if Static.objects.filter(link=link+'_2'):
    #                 link = link+'_3'
    #             else:
    #                 link = link+'_2'
    #         self.link = link
    #     super(Static, self).save()


class Parametr(models.Model):
    value = models.CharField(max_length=255)


class Review(models.Model):
    author = models.CharField(max_length=512, blank=True, null=True)
    date = models.DateTimeField(verbose_name=u'Дата публикации')
    body = models.TextField(
        help_text=u"Полная версия текста новости, будет отображаться при детальном просмотре новости.",
        verbose_name=u'Полная версия текста')
    status = models.CharField(max_length=1, choices=STATUS_REVIEW, verbose_name=u'Статус', default='2')
    color_code = models.CharField(max_length=8)

    def __str__(self):
        return self.author

    class Meta:
        verbose_name = u"Отзыв"
        verbose_name_plural = u"Отзывы"

    def save(self):
        if int(self.status) == 1:
            self.color_code = 'aa6666'
        elif int(self.status) == 2:
            self.color_code = '449944'
        elif int(self.status) == 3:
            self.color_code = 'aaaaaa'
        super(Review, self).save()

    def color_title(self):
        return '<span style="color: #%s;">%s </span>' % (self.color_code, self.author)
    color_title.allow_tags = True


class Restore(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    rdate = models.DateTimeField(auto_now_add=True)
    hash = models.CharField(max_length=255)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.user

    class Meta:
        verbose_name = u"Забытые пароли"
        verbose_name_plural = u"Забытые пароли"


class Mail(models.Model):
    link = models.CharField(verbose_name=u'Уникальное название шаблона', max_length=128, unique=True)
    title = models.CharField(verbose_name=u'Текстовое название для админки', max_length=128,)
    subject = models.CharField(verbose_name=u'Заголовок письма', max_length=256)
    body = models.TextField(verbose_name=u'Текст письма')
    type = models.IntegerField(verbose_name=u'тип', choices=((1, u'Клиентское'), (2, u'Внутреннее')))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = u"Текст письма"
        verbose_name_plural = u"Тексты писем"


class Token(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=u'Кому', on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    token = models.CharField(verbose_name=u'Токен', max_length=255, unique=True)
    dateend = models.DateTimeField(u'Дата окончания действия', null=True, blank=True)

    def __str__(self):
        return self.user.username

    @classmethod
    def generate_token(cls, user):
        n = 1
        while n <= 1:
            token_str = str(datetime.now()) + str(random.randint(1, 100000))
            token = hashlib.sha224(token_str.encode('utf-8')).hexdigest()
            if Token.objects.filter(token=token).exists():
                continue
            n += 1
        new_token = Token(
            user=user,
            token=token,
            dateend=datetime.now()+timedelta(days=7)
        )
        new_token.save()
        return new_token


class NotificationSettings(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    mail = models.ForeignKey(Mail, on_delete=models.CASCADE)
    send = models.BooleanField(default=True)

    class Meta:
        unique_together = (('user', 'mail'),)


class SubscriberListSettings(models.Model):
    subscriberlist = models.OneToOneField(campaign_models.SubscriberList, verbose_name=u'Список рассылки', on_delete=models.CASCADE)
    visible = models.BooleanField(u'Показывать в настройках подписки пользователя?', default=False)
    name = models.CharField(u'Название пункта в настройках подписки', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Настройки списка рассылки"
        verbose_name_plural = u"Настройки списков рассылки"


class Photo(models.Model):
    title = models.CharField(verbose_name=u'Название', null=True, blank=True, max_length=512)
    original_image = models.ImageField(upload_to=get_file_path)
    resize_image = ImageSpecField(source='original_image',
                                         options={'qaulity': 80},
                                         processors=[ResizeToFit(800, 600), ],)
    date = models.DateTimeField(auto_now_add=True)

    directory_string_var = 'newsfiles'

    def get_absolute_url(self):
        return '%s' % self.original_image.url

    def link(self):
        return 'https://kostochka38.ru%s' % self.original_image.url
    link.short_description = u'Ссылка'

    def photo(self):
        return '<img height="100px" src="%s">' % self.original_image.url
    photo.allow_tags = True
    photo.short_description = u'Фото'

    class Meta:
        ordering = ['-date', ]
        verbose_name = u"Фото файл"
        verbose_name_plural = u"Фото файлы"


class Menu(models.Model):
    subtitle = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Дополнительное название')
    title = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Название')
    extra_class = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Классы')
    position = models.IntegerField(default=99, verbose_name=u'Порядок')
    menu_type = models.IntegerField(choices=MENU_TYPE)
    icon = ProcessedImageField(upload_to=get_file_path,
                                         options={'qaulity': 80},
                                         processors=[ResizeToFit(800, 600), ],
                                         verbose_name=u'иконка', blank=True, null=True)
    link = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Ссылка')
    show_on_top = models.BooleanField(verbose_name=u'Показывать сверху', default=False)
    directory_string_var = 'menu'

    def __str__(self):
        return '%s - %s' % (str(self.id), self.title)

    def photo(self):
        if self.icon:
            return '<img height="100px" src="%s">' % self.icon.url
        return ' - '

    photo.allow_tags = True
    photo.short_description = u'Иконка'

    class Meta:
        ordering = ['menu_type', 'position']
        verbose_name = u"Меню"
        verbose_name_plural = u"Меню"


class Page(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    extra_class = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Классы')
    position = models.IntegerField(default=99, verbose_name=u'Порядок')
    date = models.DateTimeField(verbose_name=u'Дата публикации')
    short = RichTextField(verbose_name=u'Короткая версия', blank=True, null=True)
    body = RichTextField(verbose_name=u'Содержание')
    background = ProcessedImageField(upload_to=get_file_path,
                                     options={'qaulity': 80},
                                     processors=[ResizeToFit(800, 600), ],
                                     verbose_name=u'фон')
    list_cover = ImageSpecField(source='background', processors=[ResizeToFit(660, 1000), ],
                                options={'quality': 80})
    thumbnail = ImageSpecField(source='background', processors=[ResizeToFit(270, 200), ],
                               options={'quality': 80})

    slide_image = models.ImageField(upload_to=get_file_path, verbose_name=u'в слайдер', blank=True)
    slide_image_lazy = ImageSpecField(source='slide_image', processors=[ResizeToFit(1600, 500), ], options={'quality': 1})

    section = models.CharField(max_length=128, choices=SECTION, verbose_name=u'Раздел')
    link = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'Ссылка')
    directory_string_var = 'pages'

    def __str__(self):
        return '%s' % self.title

    def photo(self):
        return format_html('<img height="100px" src="{0}">', self.background.url)
    photo.allow_tags = True
    photo.short_description = u'фон'

    def get_absolute_url(self):
        return "/article/%s/" % self.link

    class Meta:
        ordering = ['position', ]
        verbose_name = u"Статья"
        verbose_name_plural = u"Статьи"

    def save(self):
        if not self.id and not self.link:
            link = pytils.translit.slugify(self.title)

            if Static.objects.filter(link=link):
                if Static.objects.filter(link=link+'_2'):
                    link = link+'_3'
                else:
                    link = link+'_2'
            self.link = link
        super(Page, self).save()


class SocialReview(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    date = models.DateTimeField(verbose_name=u'дата')
    short = RichTextField(verbose_name=u'текст', blank=True, null=True)
    link = models.CharField(verbose_name=u'ссылка', max_length=512, blank=True, null=True)
    screnshot = models.ImageField(upload_to=get_file_path, verbose_name=u'в слайдер', blank=True)
    cover = ImageSpecField(source='screnshot', processors=[ResizeToFit(180, 320), ],
                            options={'quality': 80})
    cover_lazy = ImageSpecField(source='screnshot', processors=[ResizeToFit(180, 320), ],
                            options={'quality': 1})
    directory_string_var = 'reviews'

    def __str__(self):
        return '%s' % self.title

    def photo(self):
        return format_html('<img src="{0}">', self.cover.url)
    photo.allow_tags = True
    photo.short_description = u'скрин'

    def get_absolute_url(self):
        return "/article/%s/" % self.link

    class Meta:
        ordering = ['-date', ]
        verbose_name = u"Отзыв"
        verbose_name_plural = u"Отзывы"


class Slide(models.Model):
    title = models.CharField(max_length=256, verbose_name=u'Название', help_text=u'выводится только в админке')

    slide_title = models.CharField(max_length=512, verbose_name=u'Заголовок', null=True, blank=True)
    slide_title_link = models.CharField(max_length=512, verbose_name=u'Ссылка заголовка', null=True, blank=True)

    slide_description = models.CharField(max_length=512, verbose_name=u'Описание', null=True, blank=True)
    slide_description_link = models.CharField(max_length=512, verbose_name=u'Ссылка с описания', null=True, blank=True)

    slide_link = models.CharField(max_length=512, verbose_name=u'Ссылка на всем слайде', null=True, blank=True)

    slide_image = models.ImageField(upload_to=get_file_path, verbose_name=u'фон', help_text=u'1600x400')
    slide_image_mobile = models.ImageField(upload_to=get_file_path, verbose_name=u'фон на мобиле', help_text=u'400x180')
    slide_admin_image = ImageSpecField(source='slide_image', processors=[ResizeToFit(320, 120), ], options={'quality': 60})
    slide_image_lazy = ImageSpecField(source='slide_image', processors=[ResizeToFit(1600, 400), ], options={'quality': 1})
    slide_image_mobile_lazy = ImageSpecField(source='slide_image_mobile', processors=[ResizeToFit(400, 180), ], options={'quality': 1})

    startdate = models.DateTimeField(verbose_name=u'Дата запуска')
    expdate = models.DateTimeField(verbose_name=u'Годен до')

    position = models.IntegerField(verbose_name=u'Позиция', default=9)

    directory_string_var = 'slides'

    def __str__(self):
        return '%s' % self.title

    def admin_slide(self):
        return '<img src="%s">' % self.slide_admin_image.url
    admin_slide.allow_tags = True
    admin_slide.short_description = u'Слайд'

    class Meta:
        ordering = ['position', ]
        verbose_name = u"Слайд-баннер"
        verbose_name_plural = u"Слайд-баннеры"


class Announcement(models.Model):

    is_active = models.BooleanField(verbose_name=u'Активно')
    text = models.TextField(verbose_name=u'Текст')
    hash = models.CharField(verbose_name='Хеш текста', max_length=32)

    class Meta:
        verbose_name = u'объявление'
        verbose_name_plural = u'Объявления'
