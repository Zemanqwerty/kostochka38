var filter_timeout = null;
var price_filter = false;
$(document).ready(function() {

    function getCookie(name) {
        let matches = document.cookie.match(new RegExp(
          "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
        ))
        return matches ? decodeURIComponent(matches[1]) : undefined
    }


    /** Проверяем, закрывал ли пользователь актуальную версию текущего объявления */

    $('.announcement').each(function () {

        const $announcement = $(this)
        
        const announcementHash = $announcement.data('announcement-hash')
        const announcementHashCookie = parseInt(getCookie('announcement_hash'), 10)

        if (typeof announcementHashCookie != 'undefined') {
            if (announcementHash != announcementHashCookie) {
                $announcement.addClass('fade in').removeClass('hidden').on('close.bs.alert', function() {
                    document.cookie = 'announcement_hash=' + announcementHash + '; max-age=31622400'
                })
            }
        }
        else {
            $announcement.addClass('fade in').removeClass('hidden').on('close.bs.alert', function() {
                document.cookie = 'announcement_hash=' + announcementHash + '; max-age=31622400'
            })
        }
    })


    /** Модельное окно с таблицей наличия товара */

    $('#availability-modal').on('show.bs.modal', function (event) {

        const $button = $(event.relatedTarget)
        const $modal = $(this)

        $modal.find('.modal-body').html('Загрузка...')

        if ($button.data('is-grouped') === false) {
            var data = {
                'item-id': $button.data('item-id')
            }
        }
        else {
            var data = {
                'is-grouped': true,
                'deckitem-id': $button.data('deckitem-id')
            }
        }

        $.get('/c/get_item_availability_table/', data)
            .done(function (response) {
                $modal.find('.modal-body').html(response)
            })
      })


    /* tool-типы в карточке товара */

    $('.view-item').find('[data-toggle="tooltip"]').tooltip({
        trigger: 'manual',
    }).tooltip('show')

    $('.catalog-goods-container li').find('[data-toggle="tooltip"]').tooltip({
        trigger: 'manual',
    })

    $(document.body).on('mouseenter', '.catalog-goods-container li', function () {
        $(this).find('[data-toggle="tooltip"].visible').tooltip('show')
    })

    $(document.body).on('mouseleave', '.catalog-goods-container li', function () {
        $(this).find('[data-toggle="tooltip"].visible').tooltip('hide')
    })

    $(".close_cookie_notification").on("click", ()=>{
        $.ajax({
            url: "/change_cookie_status/",
            success: () => {
                $(".cookie_notification").remove();
            }
        })
    });
    $('#start_autorized').click(function(){
        $('.entry').click();
        return false;
    });
    $('a#fast_login').click(function(){
        $('.entry').click();
        return false;
    });
    // открытие меню
    $('a.menu').click(function(){
        if (!$(this).hasClass('active')){
            open_left_menu();
        } else {
            close_left_menu();
        }
        return false;
    });
    $('.left-menu-layer-closer').click(function(){
        close_left_menu();
    });
    $('.left-menu-closer i').click(function(){
        close_left_menu();
    });
    function close_left_menu(){
        $('.left-menu-layer-closer').removeClass('active');
        $('.left-menu').removeClass('active');
        $('.left-menu-closer').removeClass('active');
        $('a.menu').removeClass('active');
        $('.rotate3d').removeClass('active');
        setTimeout(function(){
            $('body').removeClass('active');
        }, 600);
    }
    function open_left_menu(){
        $('.left-menu-layer-closer').addClass('active');
        $('.left-menu').addClass('active');
        $('.left-menu-closer').addClass('active');
        $('a.menu').addClass('active');
        $('.rotate3d').addClass('active');
        $('body').addClass('active');
    }
    // КОНЕЦ меню

    // открытие поиска
    $('a.btn-search').click(function(){
        if (!$(this).hasClass('active')){
            open_search_form();
        } else {
            close_search_form();
        }
        return false;
    });
    $('.search-form-layer-closer').click(function(){
        close_search_form();
    });
    $('.search-form-closer i').click(function(){
        close_search_form();
    });
    function close_search_form(){
        $('.search-form-layer-closer').removeClass('active');
        $('.search-form').removeClass('active');
        $('.search-form-closer').removeClass('active');
        $('a.search').removeClass('active');
        $('.rotate3d').removeClass('active-search');
        $('.search-input').val('');
        $('.search-result').html('').hide();
        setTimeout(function(){
            $('body').removeClass('active');
        }, 600);
    }
    function open_search_form(){
        $('.search-form-layer-closer').addClass('active');
        $('.search-form').addClass('active');
        $('.search-form-closer').addClass('active');
        $('a.search').addClass('active');
        $('.rotate3d').addClass('active-search');
        $('.search-input').focus();
        $('body').addClass('active');
    }
    // КОНЕЦ поиска

    $('.header-clipped a.menu').on('click', function(){
        $("body,html").animate({ scrollTop: 0 }, 700);
        return false;
    });
    $('.header-clipped a.search').on('click', function(){
        $("body,html").animate({ scrollTop: 0 }, 700);
        return false;
    });

    ////    search start
    $('#search_form').submit(function(){
        if($('.search-result__element.active').length > 0){
            $('.search-result__element.active')[0].click();
            return false;
        } else {
            $('#search_form').submit();
        }
    });

    $('.search-result').on('mouseover', 'a', function(){
       $('.search-result__element').removeClass('active');
    });

    $('.search-input').on('keyup', function(event){
        var val = $(this).val();

        if (val.length > 2){

            // 38, 40
            var active_search = $('.search-result__element.active');
            var active_search_first = $('.search-result__element:first');
            var active_search_last = $('.search-result__element:last');

            if(event.keyCode == 38){ // нажата клавиша вверх
                if(active_search.length > 0){ // уже нажимали клавиши навигации
                    if ( $('.search-result__element.active').is(":first-child") ){ // это и так верхний элемент, выберем последний
                        $('.search-result__element').removeClass('active');
                        active_search_last.addClass('active');
                    } else {
                        $('.search-result__element').removeClass('active');
                        active_search.prev().addClass('active');
                    }
                } else {
                    active_search_last.addClass('active');
                }
                event.preventDefault();
                event.stopPropagation();
                return false;
            }

            if(event.keyCode == 40){ // нажата клавиша вниз
                if(active_search.length > 0){ // уже нажимали клавиши навигации
                    if ($('.search-result__element.active').is(":last-child")){ // это и так нижний элемент, выберем первый

                        $('.search-result__element').removeClass('active');
                        active_search_first.addClass('active');
                    } else {
                        $('.search-result__element').removeClass('active');
                        active_search.next().addClass('active');
                    }
                } else {
                    active_search_first.addClass('active');
                }
                event.preventDefault();
                event.stopPropagation();
                return false;
            }

            $.ajax({
                type: "POST",
                url: "/search_ajax/",
                dataType: "json",
                data: 'q='+val,
                success: function (data, textStatus) {
                    if (data['result_code'] == 1){

                        $('.search-result').html('');

                        let result = '';
                        $.each(data['tags'], function(){
                            result += `
                                <div class="search-result__element tag">
                                    <a href="/c/${this['link']}/" class="search-result__element-link">
                                        ${this['title']}
                                    </a>
                                </div>
                            `;
                        })
                        $.each(data['deckitems'], function(){
                            if (this['title_en']){
                                result += `
                                    <div class="search-result__element">
                                        <a href="${this['link']}" class="search-result__element-image">${this['image']}</a>
                                        <span class="search-result__element-link">
                                            <a href="${this['link']}">${this['title']}</a><br>
                                            <small>${this['title_en']}</small><br>
                                            <small><a href="/c/${this['category_link']}/">${this['category_title']}</a></small>
                                        </span>
                                    </div>
                                `;
                            } else {
                                result += `
                                    <div class="search-result__element">
                                        <a href="${this['link']}" class="search-result__element-image">${this['image']}</a>
                                        <span class="search-result__element-link">
                                            <a href="${this['link']}">${this['title']}</a><br>
                                            <small><a href="/c/${this['category_link']}/">${this['category_title']}</a></small>
                                        </span>
                                    </div>
                                `;
                            }
                        });
                        $('.search-result').html(result).show();
                    } else {
                        if (data['error_text']){
                            $('.search-result').html('<p class="error_search">' + data['error_text'] + '</p>').show();
                        }
                    }
                }
            });
        } else {
            $('.search-result').html('').hide();
        }
        return false;
    });

    // $('.search-form').click(function (e) {
    //     if (!$(e.target).closest('a').hasClass('search-result__element')) {
    //         e.preventDefault();
    //         e.stopPropagation();
    //     }
    // });
    ////    search end


    $('.dialog-form-entry').find( "form" ).on( "submit", function( event ) {
        event.preventDefault();

        $('.dialog-form-entry .alert').removeClass('alert-danger').addClass('alert-warning').html('<i class="fa fa-spinner fa-pulse fa-fw"></i> загрузка ...').show();

        $.post('/entry/', $(this).serialize(), function(data){
            if ( data === '0'){
                setTimeout(function () {
                    $('.dialog-form-entry .alert').removeClass('alert-warning').addClass('alert-danger').html('E-mail или пароль введены не верно').show();
                }, 1000);
            } else {
                if (location.pathname === "/account/logout/complete/" || location.pathname === "/account/registration/") {
                    location.href = "https://kostochka38.ru/";
                } else {
                    window.location.reload();
                }
            }
        }, 'json');
        return false;
    });
    $('.dialog-form-recovery').find( "form" ).on( "submit", function( event ) {
        event.preventDefault();
        $('.dialog-form-recovery .alert').removeClass('alert-danger').addClass('alert-warning').html('<i class="fa fa-spinner fa-pulse fa-fw"></i> загрузка ...').show();
        $.post('/account/password/forget/', $(this).serialize(), function(data){
            // обрабатываем ответ
            if ( data ==='0'){
                setTimeout(function () {
                    $('.dialog-form-recovery .alert').removeClass('alert-warning').addClass('alert-danger').html('Пользователь с таким e-mail не найден').show();
                }, 1000);
            } else {
                $('.dialog-form-recovery .modal-footer').hide();
                $('.dialog-form-recovery .modal-body .hide-success').hide();
                $('.dialog-form-recovery .alert')
                    .removeClass('alert-danger')
                    .removeClass('alert-warning')
                    .addClass('alert-success')
                    .html('Ссылка для восстановления пароля отправлена на указанный e-mail адрес.<br>Если у Вас что-то не получится, <a href="/contacts/">напишите или позвоните</a> нам, мы поможем!').show();
            }
        }, 'json');
        return false;
    });
    $('.dialog-form-registration').find( "form" ).on( "submit", function( event ) {
        event.preventDefault();
        $('.dialog-form-registration .alert').removeClass('alert-danger').addClass('alert-warning').html('<i class="fa fa-spinner fa-pulse fa-fw"></i> загрузка ...').show();
        $.post('/account/newuser/', $(this).serialize(), function(data){
            // обрабатываем ответ
            if ( data.response === '0'){
                setTimeout(function () {
                    $('.dialog-form-registration .alert').removeClass('alert-warning').addClass('alert-danger').html(data.error.text).show();
                }, 1000);
            } else {
                $('.dialog-form-registration .alert').removeClass('alert-danger').removeClass('alert-warning').addClass('alert-success').html('Регистрация прошла успешно, перезагружаю').show();
                window.location.reload();
            }
        }, 'json');

        return false;
    });

    $('.entry').on( "click", function() {
        if ($(this).hasClass('btn-account')){
            close_left_menu();
        }
        $('#EntryModal').modal();
        return false;
    });

    $('body').on( "click", '.recovery-link', function() {
        $('#EntryModal').modal('hide');
        $('#RegistrationModal').modal('hide');

        $('#RecoveryModal').modal();
        return false;
    });
    $('.go-back-entry').on( "click", function() {
        $('#RecoveryModal').modal('hide');
        $('#RegistrationModal').modal('hide');
        setTimeout(function(){$('#EntryModal').modal();}, 500);
        return false;
    });
    $('.registration-link').on( "click", function() {
        $('#EntryModal').modal('hide');
        setTimeout(function(){$('#RegistrationModal').modal();}, 500);
        return false;
    });

    $('.repeat-btn').on( "click", function() {
        $('#RepeatOrderModal').modal();
        return false;
    });

    $('.repeat-order-confirm').on( "click", function() {
        var order_id = $('#data-order-id').val();
        location.href = '/cart/repeat/' + order_id + '/';
        return false;
    });
    //
    // END DIALOGS
    //


    //
    // CATALOG
    //
    $(document).on('click', '.weight.more .weight-link', function(){

        const $this = $(this);

        const item_id = $this.attr('data-deckitem-id');
        const iitem_id = $(this).attr('data-item_id');

        const $item_card = $('.item_block#' + item_id)

        $('li.'+item_id+' a').removeClass('active');
        $this.addClass('active');

        //var active_image_weight = $(this).find('img.light-text').clone();

        var links = $('.item_block#'+item_id+' a.title');
        if($this.hasClass('change_url')){
            history.pushState('', '', $this.data('item-url'))
        } else {
            var item_price = $(this).attr('data-price');
            $('#' + item_id + ' .price').html(item_price);
        }

        var availability = $(this).attr('data-availability');
        if (availability > 0){
            $('#no_availability_'+item_id).css('display', 'none');
            $('#go_to_cart_'+item_id).css('display', 'none');
            if (availability == 20){
                $('#add_to_cart_'+item_id).attr('data-item_id',iitem_id).css('display', 'block').addClass('presale');
                $('.item_block#'+item_id + ' div.label.presale').addClass('visible');
            } else {
                $('#add_to_cart_'+item_id).attr('data-item_id',iitem_id).css('display', 'block').removeClass('presale');
                $('.item_block#'+item_id + ' div.label.presale').removeClass('visible');
            }

        } else {
            $('#no_availability_'+item_id).css('display', 'block');
            $('#go_to_cart_'+item_id).css('display', 'none');
            $('#add_to_cart_'+item_id).css('display', 'none');
            $('.item_block#'+item_id + ' div.label.presale').removeClass('visible');
        }


        //
        // sale
        //
        if(!$(this).hasClass('change_url')){
            $('.item_block#'+item_id + ' .sale_price').removeClass('visible');
            $('.item_block#'+item_id + ' .price').removeClass('have_sale');
        }
        
        $('.item_block#' + item_id + ' .labels_block .label.action').removeClass('visible');

        if ($this.hasClass('action')) {

            var sale_price = $(this).attr('data-sale-price');
            var sale_description = $(this).attr('data-sale-description');
            var sale_value = $(this).attr('data-sale-value');
            var label = $('.item_block#' + item_id + ' .labels_block div.label.action');

            if (!$(this).hasClass('change_url')){
                $('.item_block#' + item_id + ' .sale_price').addClass('visible').html(sale_price);
                $('.item_block#' + item_id + ' .price').addClass('have_sale');
            }

            if (!label.length) {
                $('.item_block#' + item_id + ' .labels_block').append('<div class="label action" data-toggle="tooltip" data-placement="bottom"></div>');
                label = $('.item_block#' + item_id + ' .labels_block div.label.action');
                label.tooltip({trigger: 'manual'});
            }

            label
                .addClass('visible')
                .text(sale_value)
                .attr('alt', sale_description)
                .attr('title', sale_description)
                .attr('data-original-title', sale_description)
                .tooltip('show', 0);
        }
        else if ($this.hasClass('active_action')) {

            var action_description = $(this).attr('data-action-description');
            var action_link = $(this).attr('data-action-link');
            var label = $('.item_block#' + item_id + ' .labels_block a.label.action');

            if (!label.length) {
                $('.item_block#' + item_id + ' .labels_block').append('<a class="label action" data-toggle="tooltip" data-placement="bottom"></a>');
                label = $('.item_block#' + item_id + ' .labels_block a.label.action');
                label.tooltip({trigger: 'manual'});
            }
            
            label
                .addClass('visible')
                .text('%')
                .attr('href', action_link)
                .attr('title', action_description)
                .attr('data-original-title', action_description)
                .tooltip('show', 0);
        }

        $('.item_block#' + item_id + ' .labels_block .label.action:not(".visible")').tooltip('hide', 0);    

        if ($this.attr('data-is-new')) {
            $('.item_block#' + item_id + ' .label.new').addClass('visible')
        }
        else {
            $('.item_block#' + item_id + ' .label.new').removeClass('visible')
        }

        $item_card.find('.availability-block .availability').html('<a href="#" data-toggle="modal" data-target="#availability-modal" data-is-grouped="true" data-deckitem-id="' + item_id + '">' + $(this).data('availability-block-content') + '</a>')

        const $item_card_img = $item_card.find('img.main-img')
        $item_card_img.attr('src', $this.data('img-src'))

        
        $item_card.find('.view-item-link').each(function () {
            const $link = $(this)
            $link.attr('href', $this.data('item-url'))
        })

        return false;
    });
    //
    // END CATALOG
    //


    //
    // Image
    //
    $('.item-card__images__thumbnales-wrapper__img-wrapper').click(function(){
        $('.item-card__images__thumbnales-wrapper__img-wrapper').removeClass('active');
        $(this).addClass('active');

        var data_src = $(this).attr('data-src');
        var data_title = $(this).attr('data-title');

        $('.item-card__images__image img').prop('src', data_src);

        if(data_title){
            $('.item-card__images__image .image-title').show().text(data_title);
        } else {
            $('.item-card__images__image .image-title').hide();
        }
    });

    //
    // END Image
    //


    // CART
    $('.page, .page_main').on('click', '.add_to_cart', function(){
		var url="/cart/add/";
		var goods_id = $(this).attr('data-item_id');
		var real_id = $(this).attr('data-real_id');
		var content = '';
		if ($(this).hasClass('presale')){
		    content='goods_id=' + goods_id + '&presale=1';
        } else {
		    content='goods_id=' + goods_id;
		}


        $(this).css('display', 'none');
        $('#add_to_cart_waiter_'+real_id).css('display', 'block');

        var basket_of_good = $(this).attr('basket_of_good');
        if (basket_of_good == "true") {
            content += "&basket_of_good=true";
        }

		$.post(url, content, function(data){
            $('.cart-bage').show().text(data['count']);
            $('.cart-count-info').html(data['count']);
            $('.cart-sum-info').html(devSpacer(data['sum']));

            $('#add_to_cart_waiter_'+real_id).css('display', 'none');
            $('#go_to_cart_'+real_id).css('display', 'block');

            if (basket_of_good == "true") {
              send_recart(real_id, 1);
            }

            ym(23691958, 'reachGoal', 'add_to_cart');
            gtag('event', 'send', {'event_category': 'cart', 'event_action': 'add_cart'});

		}, 'json');
	});

  $('.page, .page_main').on('click', '.add_to_cart_basket_of_goods', function(){
    var url="/cart/add/";
    var goods_id = $(this).attr('data-real_id');
    console.log(goods_id);
    var real_id = $(this).attr('data-real_id');
    var content = '';
    if ($(this).hasClass('presale')){
        content='goods_id=' + goods_id + '&presale=1';
        } else {
        content='goods_id=' + goods_id;
    }

        $(this).css('display', 'none');
        $('#add_to_cart_waiter_'+real_id).css('display', 'block');

        send_recart(real_id, 1);

    $.post(url, content, function(data){
            $('.cart-bage').show().text(data['count']);
            $('.cart-count-info').html(data['count']);
            $('.cart-sum-info').html(devSpacer(data['sum']));

            $('#add_to_cart_waiter_'+real_id).css('display', 'none');
            $('.buy_text_' + real_id).css('display', 'block');

            ym(23691958, 'reachGoal', 'add_to_cart');
            gtag('event', 'send', {'event_category': 'cart', 'event_action': 'add_cart'});

    }, 'json');
  });

	$('.go_to_cart').click(function(){
        window.location.href = "/cart/"
	});

    $('#cart_table .count').change(function(){
        var count = $(this).val();
        var line_id = $(this).attr('data-lineid');
        send_recart(line_id, count);
    }).keypress(function(e) {
         if (e.keyCode < 48 || e.keyCode > 57) {
            return false;
        }
    }).keyup(function(){
        var count = $(this).val();
        var line_id = $(this).attr('data-lineid');
        send_recart(line_id, count);
    }).blur(function(){
        var count = $(this).val();
        if(count*0 == 0 && count.trim() != '' && count > 0){
            count = count;
        } else {
            count = 1;
            $(this).val(1);
        }
        var line_id = $(this).attr('data-lineid');
        send_recart(line_id, count);
    });


    $('td.td-count .count-plus').not('.disabled').on('click', function(){
        var count = $(this).parent().find('input.count').val();

        if (count > 98){
        } else {
            $(this).parent().find('input.count').val((count * 1) + 1);
            $(this).parent().find('input.count').change();
        }

        var sel = window.getSelection();
        sel.removeAllRanges();
        return false
    });
    $('td.td-count .count-minus').not('.disabled').on('click', function(){
        var count = $(this).parent().find('input.count').val();
        var line_id = $(this).parent().find('input.count').attr('data-lineid');

        if (count < 2){
        } else {
            $(this).parent().find('input.count').val((count * 1) - 1);
            $(this).parent().find('input.count').change();
        }

        var sel = window.getSelection();
        sel.removeAllRanges();
        return false
    });

    $('.cart_line .delete i').click(function(){
        var line_id = $(this).parent().attr('data-lineid');
        send_recart(line_id, 0);
    });

    $('#next_button').click(function(){
       $('#registration_cart_form').submit();
    });
    // END CART

    $('.scroll_on_top').on('click', function(){
        $("body,html").animate({ scrollTop: 0 }, 700);
    });

    $('.refresh-captcha').click(function(){
        var $form = $(this).parents('form');
        $.getJSON('/captcha/refresh/', {}, function(json) {
            $form.find('#id_captcha_0').attr('value', json.key);
            $form.find('img.captcha').attr('src', json.image_url);
        });

        return false;
    });

    //  загружкаем аяксом следующую страницу
    $('.load-next-page').on('click', 'a', function(){
        if ($(this).hasClass('disabled')){
            return false;
        }
        locked_ajax_element();
        $(this).hide();
        $('.load-next-page .loader').show();
        var filter_data = {
            'ajax_page': true,
            'page': $('#data-page').val(),
        };
        if (price_filter){
            filter_data['price'] =  $('#price-range').val();
        }
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще
                $('.load-next-page').html(data['next_page_button']);

                //  новая страница товаров
                $('.catalog-goods-container').append("<div class='next-page-container page-" + data['page'] +"'></div>");
                $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    //  загружкаем аяксом сортировку
    $('.page').on('change', '.sort_wrapper select', function(){
        $('.sort_wrapper option').removeClass('active');
        $('.sort_wrapper option:selected').addClass('active');

        if ($(this).hasClass('disabled')){
            return false
        }

        locked_ajax_element();
        $('.paginator').html();
        $('.load-next-page').html();

        $('.item_block').remove();
        $('.next-page-container').remove();
        $('.catalog-goods .ajax-waiter').show();

        var filter_data = {
            'ajax_page': true,
            'sort': $('.sort_wrapper option:selected').attr('value')
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);
                price_filter = false;
                // удаляем лоадер
                $('.catalog-goods .ajax-waiter').hide();

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще
                $('.load-next-page').html(data['next_page_button']);

                if (price_filter){
                    filter_data['price'] =  $('#price-range').val();
                }

                //  новая страница товаров
                $('.catalog-goods-container')
                    .hide()
                    .append(data['items'])
                    .fadeIn('500');

                $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    //  загружкаем аяксом группировку товаров
    $('.page').on('change', '#group-catalog-button', function(){

        if ($(this).prop('checked')){
            var catalog_group_view = 'group';
            $('.sort_wrapper').addClass('disable');
        } else {
            var catalog_group_view = 'no-group';
            $('.sort_wrapper').removeClass('disable');
        }

        if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }

        locked_ajax_element();
        $('.paginator').html();
        $('.load-next-page').html();

        $('.item_block').remove();
        $('.next-page-container').remove();
        $('.item-filter-panel').css('opacity', 0.3);
        $('.catalog-goods .ajax-waiter').show();

        var filter_data = {
            'ajax_page': true,
            'catalog_group_view': catalog_group_view
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);
                price_filter = false;
                // удаляем лоадер
                $('.catalog-goods .ajax-waiter').hide();

                // новые фильтры
                $('.item-filter-panel').css('opacity', 1).html(data['filters']);
                $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще
                $('.load-next-page').html(data['next_page_button']);

                //  новая страница товаров
                $('.catalog-goods-container')
                    .hide()
                    .append(data['items'])
                    .fadeIn('500');

                $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    //  загружкаем аяксом отображение товаров нет в наличии
    $('.page').on('change', '#show-availability-button', function(){

        if ($(this).prop('checked')){
            var show_availability = 'show';
        } else {
            var show_availability = 'hide';
        }

        if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }

        locked_ajax_element();
        $('.paginator').html();
        $('.load-next-page').html();

        $('.item_block').remove();
        $('.next-page-container').remove();
        $('.item-filter-panel').css('opacity', 0.3);
        $('.catalog-goods .ajax-waiter').show();

        var filter_data = {
            'ajax_page': true,
            'show_availability': show_availability
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);
                price_filter = false;
                // удаляем лоадер
                $('.catalog-goods .ajax-waiter').hide();

                // новые фильтры
                $('.item-filter-panel').css('opacity', 1).html(data['filters']);
                $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще"
                $('.load-next-page').html(data['next_page_button']);

                //  новая страница товаров
                $('.catalog-goods-container')
                    .hide()
                    .append(data['items'])
                    .fadeIn('500');

                $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    //  загружкаем аяксом новинки
    $('.page').on('change', '#show-new-button', function(){

        if ($(this).prop('checked')){
            var show_new = true;
        } else {
            var show_new = false;
        }

        if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }

        locked_ajax_element();
        $('.paginator').html();
        $('.load-next-page').html();

        $('.item_block').remove();
        $('.next-page-container').remove();
        $('.item-filter-panel').css('opacity', 0.3);
        $('.catalog-goods .ajax-waiter').show();

        var filter_data = {
            'ajax_page': true,
            'show_new': show_new
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);
                price_filter = false;
                // удаляем лоадер
                $('.catalog-goods .ajax-waiter').hide();

                // новые фильтры
                $('.item-filter-panel').css('opacity', 1).html(data['filters']);
                $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще"
                $('.load-next-page').html(data['next_page_button']);

                //  новая страница товаров
                $('.catalog-goods-container')
                    .hide()
                    .append(data['items'])
                    .fadeIn('500');

                $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    //  загружкаем аяксом фильтры
    $('.item-filter-panel').on('change', '.list-group-item input', function(e) {
        var filter_data = {
            'ajax_page': true
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }
        // $('.paginator').html();
        // $('.load-next-page').html();
        $('.filter-div').addClass('opacity');

        clearTimeout(filter_timeout);
        filter_timeout = setTimeout(() => {
            $('.item_block').css({'visibility': 'hidden'});
            $('.item-filter-panel').css('opacity', 0.3);
            locked_ajax_element();
            $('.catalog-goods .ajax-waiter').show();
            $.ajax({
                type: "GET",
                url: $('#data-link').val(),
                data: filter_data,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    $('#data-filters').val(data['data_filters']);
                    $('#data-link').val(data['data_link']);
                    $('#data-page').val(data['data_page']);
                    price_filter = false;
                    // удаляем лоадер
                    $('.catalog-goods .ajax-waiter').hide();

                    // новые фильтры
                    $('.side-filter-panel').css('opacity', 1).html(data['filters']);
                    $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);
                    // $('select.chosen-select').chosen( {allow_single_deselect: true} );
                    // $('select.chosen-select-deselect').chosen( {allow_single_deselect: true} );

                    //  новый пагинатор
                    $('.paginator').html(data['paginator']);

                    //  новая кнопка "показать еще
                    $('.load-next-page').html(data['next_page_button']);
                    //  новая страница товаров
                    $('.item_block').remove();
                    $('.catalog-goods-container')
                        .hide()
                        .append(data['items'])
                        .fadeIn('500');

                    $('.owl-carousel.tags').owlCarousel({
                        nav:true,
                        loop: false,
                        autoWidth: true,
                        margin:10,
                    })

                    // изменяем урл
                    history.pushState('', '', data['link']);

                    unlocked_ajax_element();
                },
                error: function(jqXHR, textStatus, errorThrown){
                    console.log(textStatus);
                }
            });
        }, 1000);

        return false;
    });

    //  загружкаем аяксом тэги
    $('.item-filter-panel-tag').on('change', '.checkbox.tags input', function(e) {
        var filter_data = {
            'ajax_page': true
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }
        // $('.paginator').html();
        // $('.load-next-page').html();
        $('.filter-div').addClass('opacity');

        clearTimeout(filter_timeout);
        filter_timeout = setTimeout(() => {
            $('.item_block').css({'visibility': 'hidden'});
            $('.item-filter-panel').css('opacity', 0.3);
            locked_ajax_element();
            $('.catalog-goods .ajax-waiter').show();
            $.ajax({
                type: "GET",
                url: $('#data-link').val(),
                data: filter_data,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    $('#data-filters').val(data['data_filters']);
                    $('#data-link').val(data['data_link']);
                    $('#data-page').val(data['data_page']);
                    price_filter = false;
                    // удаляем лоадер
                    $('.catalog-goods .ajax-waiter').hide();

                    // новые фильтры
                    $('.side-filter-panel').css('opacity', 1).html(data['filters']);
                    $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);
                    // $('select.chosen-select').chosen( {allow_single_deselect: true} );
                    // $('select.chosen-select-deselect').chosen( {allow_single_deselect: true} );

                    //  новый пагинатор
                    $('.paginator').html(data['paginator']);

                    //  новая кнопка "показать еще
                    $('.load-next-page').html(data['next_page_button']);
                    //  новая страница товаров
                    $('.item_block').remove();
                    $('.catalog-goods-container')
                        .hide()
                        .append(data['items'])
                        .fadeIn('500');

                    $('.owl-carousel.tags').owlCarousel({
                        nav:true,
                        loop: false,
                        autoWidth: true,
                        margin:10,
                    })

                    // изменяем урл
                    history.pushState('', '', data['link']);

                    unlocked_ajax_element();
                },
                error: function(jqXHR, textStatus, errorThrown){
                    console.log(textStatus);
                }
            });
        }, 1000);

        return false;
    });

    //  загружкаем аяксом новую страницу
    $('.paginator').on('click', 'a.ajax', function(e) {
        if ($(this).hasClass('disabled')){
            return false
        }

        locked_ajax_element();
        $('.item_block').remove();
        $('.next-page-container').remove();
        $('.catalog-goods .ajax-waiter').show();
        $("body,html").animate({ scrollTop: 300 }, 200);

        $('.item-filter-panel').addClass('opacity');


        var filter_data = {
            'ajax_page': true,
            'page': $(this).attr('data-page')
        };
        if (price_filter){
            filter_data['price'] =  $('#price-range').val();
        }
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        $.ajax({
            type: "GET",
            url: $('#data-link').val(),
            data: filter_data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                $('#data-filters').val(data['data_filters']);
                $('#data-link').val(data['data_link']);
                $('#data-page').val(data['data_page']);

                // удаляем лоадер
                $('.catalog-goods .ajax-waiter').hide();

                //  новый пагинатор
                $('.paginator').html(data['paginator']);

                //  новая кнопка "показать еще
                $('.load-next-page').html(data['next_page_button']);

                //  новая страница товаров
                $('.catalog-goods-container')
                    .hide()
                    .append(data['items'])
                    .fadeIn('500');

                // изменяем урл
                history.pushState('', '', data['link']);

                unlocked_ajax_element();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
            }
        });
        return false;
    });

    $('.hovered .food-menu__element__link').click(function(){
        return false;
    });
    $('.clicked .food-menu__element__link').click(function(){
        $('.food-menu__submenu').hide();
        $('.close-food-menu__submenu').hide();
        // $('.arrow-top').hide();
        $(this).parent().find('.food-menu__submenu').show()
            .parent().find('.close-food-menu__submenu').show();
            // .parent().find('.arrow-top').show();
        return false;
    });
    $('.close-food-menu__submenu').click(function(){
        $('.food-menu__submenu').hide();
        $('.close-food-menu__submenu').hide();
        // $('.arrow-top').hide();
    });

    $('.food-menu__element__link').click(function () {
        return false;
    });

    $('a.food-menu__element__link').click(function (e) {
        var current_link = this;
        if ($('.animenu__nav').hasClass('animenu__nav--open')) {
            $(current_link).parent().find('.animenu__nav__child').toggle();
        }
    });

    //  отображение фильтров в мобильной версии
    $('.page').on('click', '.show-filter', function(){
        $('.filter-wrapper').toggleClass('hidden-xs show-xs');
        $('.sort_wrapper').toggleClass('hidden-xs show-xs');
        if($('.filter-wrapper').hasClass('show-xs')){
            $('.show-filter').text('Закрыть').removeClass('btn-info').addClass('btn-danger');
        } else {
            $('.show-filter').text('Фильтры').addClass('btn-info').removeClass('btn-danger');
        }
        return false;
    });

    $('.wrapper_show_aditional').click(function () {
        $(this).hide();
        $('.cart_registration .aditional').show('fast');
        return false;
    });

    $('.no_need_registration').change(function () {
        $('.registratopn_wrapper').toggleClass('hidden');
        $('.online-pay').toggleClass('hidden');
        if ($('.online-pay').hasClass('hidden')){
            $('.cash-pay').prop('selected', 'true')
        }

    });

    // сбрр статистики
    $('.container').on('click', '.statistics input', function () {
        if ($(this).prop('checked')) {
            $.ajax({
            type: "POST",
            url: '/put_statistics/',
            data: {
                'name': $(this).prop('name'),
                'value': $(this).prop('value'),
                'id': $(this).attr('data-id')
            },
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
            },
            error: function(jqXHR, textStatus, errorThrown){
            }
        });

        }
    });

    $('.lazy').Lazy();

    var mobile_banner = false;
    if ($('body').width() < 768) {
        mobile_banner = true;
    }

    var royal_banner = $('.start-banner');
    if (mobile_banner) {
        royal_banner.attr("src", royal_banner.data('src-mobile')).addClass('royal-mobile');
    } else {
        royal_banner.attr("src", royal_banner.data('src')).addClass('royal-pc');
    }
    $('#banners').on('slide.bs.carousel', function (ev) {
        var lazy;
        if (mobile_banner){
            lazy = $(ev.relatedTarget).find("img[data-src-mobile]");
            lazy.attr("src", lazy.data('src-mobile'));
        } else {
            lazy = $(ev.relatedTarget).find("img[data-src]");
            lazy.attr("src", lazy.data('src'));
        }
        lazy.removeAttr("data-src").removeAttr("data-src-mobile");
    });


    $('.open-review-modal').click(function () {
        var target = $(this).data('target-custom');
        var lazy = $(target).find('img[data-src]');
        if (lazy){
            lazy.attr('src', lazy.data('src'));
            lazy.removeAttr('data-src');
        }
        console.log(target);
        $(target).modal();
        return false;
    })
});

function activate_price_range(min, max, from, to) {
    $("#price-range").ionRangeSlider({
        type: "double",
        //grid: true,
        min: min,
        max: max,
        from: from,
        to: to,
        step: 10,
        input_values_separator: '-',
        postfix: " р.",
        prettify_separator: " ",
        onFinish: function (data) {
            load_price_sort();
        }
    });
}

function load_price_sort() {
     if ($('.item-filter-panel').hasClass('disabled')){
            return false
        }

        var filter_data = {
            'ajax_page': true,
            'price': $('#price-range').val()
        };
        $('.list-group-item input:checkbox:checked').each(function(){
            if (filter_data[$(this).prop('name')]){
                filter_data[$(this).prop('name')] += ',' + $(this).val();
            } else {
                filter_data[$(this).prop('name')] = $(this).val();
            }
        });

        clearTimeout(filter_timeout);
        filter_timeout = setTimeout(() => {
            locked_ajax_element();
            $('.paginator').html();
            $('.load-next-page').html();

            $('.item_block').remove();
            $('.item-filter-panel').css('opacity', 0.3);
            $('.catalog-goods .ajax-waiter').show();

            $.ajax({
                type: "GET",
                url: $('#data-link').val(),
                data: filter_data,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    $('#data-filters').val(data['data_filters']);
                    $('#data-link').val(data['data_link']);
                    $('#data-page').val(data['data_page']);
                    if(data['price_filter']){
                        price_filter = true;
                    } else {
                        price_filter = false;
                    }
                    // удаляем лоадер
                    $('.catalog-goods .ajax-waiter').hide();

                    // новые фильтры
                    $('.item-filter-panel').css('opacity', 1).html(data['filters']);
                    $('.item-filter-panel-tag').css('opacity', 1).html(data['tag_filters']);

                    //  новый пагинатор
                    $('.paginator').html(data['paginator']);

                    //  новая кнопка "показать еще
                    $('.load-next-page').html(data['next_page_button']);

                    //  новая страница товаров
                    $('.catalog-goods-container')
                        .hide()
                        .append(data['items'])
                        .fadeIn('500');

                    $('.owl-carousel.tags').owlCarousel({
                        nav:true,
                        loop: false,
                        autoWidth: true,
                        margin:10,
                    })

                    $(".page-" + data['page']).hide().append(data['items']).fadeIn('500');

                    // изменяем урл
                    history.pushState('', '', data['link']);

                    unlocked_ajax_element();

                },
                error: function(jqXHR, textStatus, errorThrown){
                    console.log(textStatus);
                }
            });
        }, 200);
        return false;
}
function locked_ajax_element(){
    // заблокируем все ajax элементы
    $('.paginator a').addClass('disabled');
    $('.paginator').hide();
    $('.load-next-page a').addClass('disabled').hide();
    $('.item-filter-panel').addClass('disabled').css('opacity', 0.3);
}

function unlocked_ajax_element(){
    //  заблокируем все ajax элементы
    $('.paginator a').removeClass('disabled');
    $('.paginator').show();
    $('.load-next-page a').removeClass('disabled').show();
    $('.item-filter-panel').removeClass('disabled').css('opacity', 1);
    $('.lazy').Lazy();
}

function send_recart(id, count){
    var data = {'id': id, 'count': count};
    console.log("DDD");

//    // изменить хэш для метрики
//    window.location.hash = 'editing_cart';

    ajaxPost('/edit_cart_line/', data,'json',
        function(data, textStatus, jqXHR){
            if (data['need_reload']){
                location.reload();
            }
            if (data['count'] == 0){
                $('#line_'+id).hide('fast');
                setTimeout(function(){
                    $('#line_'+id).remove();

                    if ($('.cart_line.items').length == 0 ){
                        $('#my_cart_form').hide();
                        $('.empty_cart').show();
                    }
                }, 1000);
            } else {
                $('#line_'+id+' .price span.price_price').html(devSpacer(data['line_summ']).replace(' . ', ',') + ' <i class="far fa-ruble-sign"></i>');
                if (data['real_line_summ']){
                    $('#line_'+id+' .price span.real_price').html(devSpacer(data['real_line_summ']).replace(' . ', ',') + ' <i class="far fa-ruble-sign"></i>');
                }
            }

            $('#summ_s_dostavkoy').html(devSpacer(data['real_zakaz_sum']).replace(' . ', ','));
            $('#dostavka').html(devSpacer(data['dostavka']).replace(' . ', ','));
            $('#skidka').html(devSpacer(data['skidka']).replace(' . ', ','));
            $('#summ_so_skidkoi').html(devSpacer(data['summ_so_skidkoi']).replace(' . ', ','));
            if (data['skidka_na_meloch'] > 0){
                $('#skidka_na_meloch').html(devSpacer(data['skidka_na_meloch']).replace(' . ', ','));
                $('.wrapper_for_skidka_na_meloch').show();
            } else {
                $('.wrapper_for_skidka_na_meloch').hide();
            }


        },
        function(jqXHR, textStatus, errorThrown){});
    return false;
}

function pre_submit(){
    $('#type').val(1);
    $('#my_cart_form').submit();
}

function full_submit(){
    $('#type').val(2);
    $('#my_cart_form').submit();
}


function ajaxPost(url, data, type, ajaxSuccess, ajaxError){
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        dataType: type,
        success: ajaxSuccess,
        error: ajaxError
    });
}

function devSpacer(number)
{
    number = ' '+ number;
    return number.replace(/(\d{1,3})(?=((\d{3})*([^\d]|$)))/g, " $1 ");
}

$(document).scroll(function(){
   if($(document).scrollTop() > 150){
       $('.scroll_on_top').fadeIn(500);
       $('.header-clipped').show();
   } else {
       $('.scroll_on_top').fadeOut(150);
       $('.header-clipped').hide();
   }
});

$('a').blur();

// CSS3 animated & responsive dropdown menu
(function(){
  var animenuToggle = document.querySelector('.animenu__toggle'),
      animenuNav    = document.querySelector('.animenu__nav'),
      hasClass = function( elem, className ) {
        return new RegExp( ' ' + className + ' ' ).test( ' ' + elem.className + ' ' );
      },
      toggleClass = function( elem, className ) {
        var newClass = ' ' + elem.className.replace( /[\t\r\n]/g, ' ' ) + ' ';
        if( hasClass(elem, className ) ) {
          while( newClass.indexOf( ' ' + className + ' ' ) >= 0 ) {
            newClass = newClass.replace( ' ' + className + ' ' , ' ' );
          }
          elem.className = newClass.replace( /^\s+|\s+$/g, '' );
        } else {
          elem.className += ' ' + className;
        }
      },
      animenuToggleNav =  function (){
        toggleClass(animenuToggle, "animenu__toggle--active");
        toggleClass(animenuNav, "animenu__nav--open");
      };

  if (!animenuToggle.addEventListener) {
      animenuToggle.attachEvent("onclick", animenuToggleNav);
  }
  else {
      animenuToggle.addEventListener('click', animenuToggleNav);

  }
})();

$(document).ready(function(){
    $('.owl-carousel.tags').owlCarousel({
    nav:true,
    loop: false,
    autoWidth: true,
    margin:10,
    // responsive:{
    //     0:{
    //         items:2
    //     },
    //     600:{
    //         items:4
    //     },
    //     1000:{
    //         items:8
    //     }
    // }
  })
  $('.tags.owl-prev').click(() => $('.owl-carousel.tags').trigger('next.owl.carousel'))
  $('.tags.owl-next').click(() => $('.owl-carousel.tags').trigger('prev.owl.carousel'))

  $('.owl-carousel:not(.tags):not(.producer-block-main)').owlCarousel({
    nav:false,
    loop: false,
    margin:20,
    responsive:{
        0:{
            items:1
        },
        600:{
            items:2
        },
        1000:{
            items:4
        }
    }
  })
  $('.owl-carousel.producer-block-main').owlCarousel({
    nav:false,
    loop: false,
    margin:20,
    responsive:{
        0:{
            items:1
        },
        500:{
            items:2
        },
        800:{
            items:3
        },
        1000:{
            items:4
        },
        1200:{
            items:5
        }
    }
  })
})


$(document).ready(function () {
    $(".dont_show_again_button_account").on("click", function () {
        $.ajax({
            url: "/change_basket_of_goods_status/",
            success: function () {
                $('.goods_items_block').remove();
            }
        });
    });
});