# -*- coding: utf-8 -*-
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext, loader, Context
from news.forms import CommentForm
from news.models import *
from catalog.models import ItemSale, Deckitem
from django import forms
from captcha.fields import CaptchaField
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


class CaptchaForm(forms.Form):
    captcha = CaptchaField()


class CommentForm(forms.Form):
    captcha = CaptchaField()   


def static_information(request):
    back_link = request.META['HTTP_REFERER']
    current_link = 'news'

    response = render(request, 'news_info.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def static_information_2(request):
    back_link = False
    if 'HTTP_REFERER' in request.META:
        back_link = request.META['HTTP_REFERER']
    current_link = 'promo'

    response = render(request, 'action_info.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def news_inner(request, link, page=1):
    current_link = 'news'

    if request.user.is_staff:
        new = get_object_or_404(New, link=link)
    else:
        new = get_object_or_404(New, link=link, status=2)

    if new.action:
        return HttpResponsePermanentRedirect('/promo/%s' % link)

    response = render(request, 'news_comment.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def news(request, page=1):
    element_to_page = 10
    if 'page' in request.GET:
        page = int(request.GET['page'])

    start_query = int(page)*int(element_to_page) - int(element_to_page)
    stop_query = int(page)*int(element_to_page)

    iteration_count = 0

    if request.user.is_staff:
        news_count = New.objects.filter(status__in=[1, 2], action=False).count()
        result_count = news_count
        news_items = New.objects.filter(status__in=[1, 2], action=False)
        query = news_items
    else:
        news_count = New.objects.filter(status=2, action=False).count()
        result_count = news_count
        news_items = New.objects.filter(status=2, action=False)
        query = news_items

    page_var = {'pages': []}

    if result_count > 20:
        result = query[start_query:stop_query]
        if result_count % element_to_page:
            iteration_count = result_count / element_to_page + 1
        else:
            iteration_count = result_count / element_to_page
        page_var['page_count'] = iteration_count

        if page == 1:  # первая страница
            page_var['next_page'] = page+1
            page_var['first_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
            else:
                page_var['page_count'] = iteration_count

            for i in range(int(page_var['page_count'])):
                page_var['pages'].append(i+1)

        elif page == iteration_count:  # последняя страница
            page_var['prev_page'] = page-1
            page_var['not_next_page'] = True
            page_var['last_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            elif iteration_count == 3:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            else:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-1+i)


        else:  # промежуточная страница
            page_var['next_page'] = page+1
            page_var['prev_page'] = page-1
            page_var['page_count'] = 5
            for i in range(int(page_var['page_count'])):
                this_page = page-2+i
                if this_page > 0 and this_page <= iteration_count:
                    page_var['pages'].append(page-2+i)

    else:
        result = query
        stop_query = result_count

    if stop_query > result_count:
        stop_query = result_count

    news_items = result
    pages = range(iteration_count)

    start_item = start_query
    end_item = stop_query

    current_link = 'news'
    response = render(request, 'news.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def action_inner(request, link):

    if request.user.is_staff:
        action = get_object_or_404(New, link=link, action=True)
    else:
        action = get_object_or_404(New, link=link, action=True, status=2)

    form = CommentForm(request.POST or None)
    errors = {}
    data = {}
    if request.method == 'POST':
        if request.POST['name'].strip():
            data['name'] = request.POST['name'].strip()
        else:
            errors['name'] = 'true'

        if request.POST['text'].strip():
            data['text'] = request.POST['text'].strip()
        else:
            errors['text'] = 'true'

        if not errors and form.is_valid():
            new_comment = Comment(
                owner_id=1,
                author=data['name'],
                new_id=action.id,
                body=data['text'],
                status=1
            )
            new_comment.save()

            ## высылаем на почту информатор об комменте
            subject_template = loader.get_template('subj_comment.txt')
            message_template = loader.get_template('mess_comment.txt')
            subject_context = Context({})
            message_context = Context({
                'new_comment': new_comment,
                'new': action
            })
            subject = subject_template.render(subject_context)
            message = message_template.render(message_context)
            send_mail(subject, message, settings.SENDER_EMAIL, [settings.REVIEW_EMAIL], fail_silently=True)

            return redirect('/promo/comment-add-complete/', link=link)
        else:
            errors['captcha'] = 'true'

    comments = Comment.objects.filter(new=action.id, status=2).order_by('date').values()
    number = 1
    for comment in comments:
        comment['number'] = number
        number += 1

    response = render(request, 'action_comment.html', {
        'form': form,
        "new": action,
        'errors': errors,
        'data': data,
        'comments': comments,
        'current_link': 'promo'
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def action(request):
    news = New.objects.filter(status=2, action=True, complete=False, exp_date__gte=datetime.datetime.now())
    flatpage = get_object_or_404(Static, link='promo')

    # itemsales = ItemSale.objects\
    #     .filter(date_end__gte=datetime.datetime.now(), show=True)\
    #     .order_by('-sale')\
    #     .select_related('item', 'item__deckitem')\
    #     .values_list('item__deckitem__id', flat=True)
    #
    # items = Deckitem.objects.filter(id__in=itemsales, active=True).distinct()
    #
    # items = dict([(obj.id, obj) for obj in items])
    # sorted_items = []
    # idlist = []
    # for id in itemsales:
    #     if not id in idlist:
    #         sorted_items.append(items[id])
    #         idlist.append(id)
    # items = sorted_items

    current_link = 'promo'
    response = render(request, 'action.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def article_inner(request, link):
    if request.user.is_superuser:
        article_element = get_object_or_404(Page, link=link)
    else:
        article_element = get_object_or_404(Page, link=link, date__lte=datetime.datetime.now())
    response = render(request, 'article_comment.html', {
        "article": article_element,
        'current_link': 'article'
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def article(request):
    element_to_page = 10
    page = 1
    if 'page' in request.GET:
        page = int(request.GET['page'])

    start_query = int(page)*int(element_to_page) - int(element_to_page)
    stop_query = int(page)*int(element_to_page)

    iteration_count = 0

    if request.user.is_superuser:
        articles_count = Page.objects.all().order_by('-date').count()
        result_count = articles_count
        articles_items = Page.objects.all().order_by('-date')
        query = articles_items
    else:
        articles_count = Page.objects.filter(date__lte=datetime.datetime.now()).order_by('-date').count()
        result_count = articles_count
        articles_items = Page.objects.filter(date__lte=datetime.datetime.now()).order_by('-date')
        query = articles_items

    page_var = {'pages': []}

    if result_count > 15:
        result = query[start_query:stop_query]
        if result_count % element_to_page:
            iteration_count = result_count / element_to_page + 1
        else:
            iteration_count = result_count / element_to_page
        page_var['page_count'] = iteration_count

        if page == 1:  # первая страница
            page_var['next_page'] = page+1
            page_var['first_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
            else:
                page_var['page_count'] = iteration_count

            for i in range(int(page_var['page_count'])):
                page_var['pages'].append(i+1)

        elif page == iteration_count:  # последняя страница
            page_var['prev_page'] = page-1
            page_var['not_next_page'] = True
            page_var['last_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            elif iteration_count == 3:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            else:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-1+i)

        else:  # промежуточная страница
            page_var['next_page'] = page+1
            page_var['prev_page'] = page-1
            page_var['page_count'] = 5
            for i in range(int(page_var['page_count'])):
                this_page = page-2+i
                if this_page > 0 and this_page <= iteration_count:
                    page_var['pages'].append(page-2+i)

    else:
        result = query.order_by('-date')
        stop_query = result_count

    if stop_query > result_count:
        stop_query = result_count

    articles = result
    pages = range(iteration_count)

    start_item = start_query
    end_item = stop_query
    current_link = 'article'

    response = render(request, 'article.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response
