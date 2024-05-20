$(function (){
    $(".paytype-checkbox").on('change', function(){
        var value = $(this).val();
        if (value == 4){
            $(".payment_notification").removeClass('hidden');
        } else {
            $(".payment_notification").addClass('hidden');
        }
    });
    $(".delivery-checkbox").on('change', function(){
        var value = $(this).val();
        if (value == "-1"){
            $(".delivery_notification").addClass('hidden');
        } else {
            $(".delivery_notification").removeClass('hidden');
        }
    })
});