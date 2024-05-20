(function($){
    $(document).ready(function(){
        // раз в 5 секунд проверяем заказ на изменения, если есть изменения - блокируем сохранеие.
        var zakaz_checker_interval = setInterval(function() {
            if (location.pathname !== "/DgJrfdJg/catalog/insidezakaz/") {
                var content_type_id = 45;

                $.ajax({
                    type: "POST",
                    url: '/check_zakaz_state/',
                    data: {'object_id': $('#zakaz_id').val(), 'load_date': $('#zakaz_date').val(), 'content_type_id': content_type_id},
                    dataType: 'json',
                    success: function (data) {
                        if (data['response'] === 1){
                            console.log('Заказ изменили! Блокируем сохранение.');
                            submit_row_hidden();
                            clearInterval(zakaz_checker_interval);

                            console.log(data['comment']);
                            $('#update-comment').html(data['comment']);

                            console.log(data['version_user']);
                            $('#update-username').html(data['version_user']);
                        }
                        if (data['response'] === 0){
                            console.log('Заказ не изменен.');
                        }
                    },
                    error: function(error){
                        console.log('Какая-то ошибка');
                        console.log(error);
                    }
                });
            }
        }, 5000);


        $('.btn-update').click(function () {
            window.location.reload();
        });

        $('#content-main').on('submit', "#_form.stoped", (function () {
            return false;
        }));
    });

    function submit_row_hidden () {
        $('.submit-row').hide();
        $('.js-inline-admin-formset').hide();
        $('.update-layer').show();

        $('.module.aligned ').css('opacity', '0.3');
        $('#_form').addClass('stoped'); 
    }

})(django.jQuery);

