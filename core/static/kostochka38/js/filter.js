/**
 * Created by Vanger on 26.07.14.
 */
setTimeout( function(){

    $('#changelist-filter')
        .addClass('hide').find('h3').hide().end()
        .find('ul').hide().end()
        .find('h2').text('Показать');

    $('#content-main')
        .on('click', '#changelist-filter.hide', function(){
            $('#changelist-filter')
                .removeClass('hide').addClass('show').find('h3').show().end()
                .find('ul').show().end()
                .find('h2').text('СКРЫТЬ');
        })
        .on('click', '#changelist-filter.show', function(){
            $('#changelist-filter')
                .removeClass('show').addClass('hide').find('h3').hide().end()
                .find('ul').hide().end()
                .find('h2').text('Показать');
        });

}
, 1000);
