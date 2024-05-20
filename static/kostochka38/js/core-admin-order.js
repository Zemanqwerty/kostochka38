/***
 *  Скрипт для автосворачивания changelist-filter на странице заказов в админке
 * */

  (function($){ $(document).ready(function(){

    $('#show-filters').hide();

    var show_fltr_txt = 'Показать фильтры \u25BD';
    var hide_fltr_txt = 'Скрыть фильтры';

    $('#changelist-filter h2').html('<a style="color: white; display: inline-block; height: 30px; line-height: 30px;" id="hide-filters" href="#">' + show_fltr_txt + '</a>');

    $('#hide-filters').bind('click', function() {
        if ($('#changelist').hasClass('filtered')){
            $('#hide-filters').text(show_fltr_txt);
        } else {
            $('#hide-filters').text(hide_fltr_txt);
        }
        $('#changelist-filter h2').siblings().not('style').toggle();
        $('#changelist').toggleClass('filtered');
    });

    hide_filters(); // при загрузке страницы фильтры должны быть скрыты

    function hide_filters(){
        $('#show-filters').show();
        $('#changelist').removeClass('filtered');
        $('#changelist-filter h2').siblings().hide();
    }
  });
})(django.jQuery);