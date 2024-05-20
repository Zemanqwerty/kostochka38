$(document).ready(function() {
    var phoneInputs = document.querySelectorAll('#phone');

    var getInputNumbersValue = function (input) {
        return input.value.replace(/\D/g, '');
    }

    var onPhonePaste = function (e) {
        var input = e.target,
            inputNumbersValue = getInputNumbersValue(input);
        var pasted = e.clipboardData || window.clipboardData;
        if (pasted) {
            var pastedText = pasted.getData('Text');
            if (/\D/g.test(pastedText)) {
                // Если ввели не числа - удаляем такие символы,
                input.value = inputNumbersValue;
                return;
            }
        }
    }

    var onPhoneInput = function (e) {
        var input = e.target,
            inputNumbersValue = getInputNumbersValue(input),
            selectionStart = input.selectionStart,
            formattedInputValue = "";

        if (!inputNumbersValue) {
            return input.value = "";
        }

        if (input.value.length != selectionStart) {
            // Редактирование символов в середине
            if (e.data && /\D/g.test(e.data)) {
                // Если ввели не число
                input.value = inputNumbersValue;
            }
            return;
        }

        if (["7", "8", "9"].indexOf(inputNumbersValue[0]) > -1) {
            if (inputNumbersValue[0] == "9") inputNumbersValue = "7" + inputNumbersValue;
            var firstSymbols = (inputNumbersValue[0] == "8") ? "+7" : "+7";
            formattedInputValue = input.value = firstSymbols;
            if (inputNumbersValue.length > 1) {
                formattedInputValue += '(' + inputNumbersValue.substring(1, 4);
            }
            if (inputNumbersValue.length >= 5) {
                formattedInputValue += ')' + inputNumbersValue.substring(4, 7);
            }
            if (inputNumbersValue.length >= 8) {
                formattedInputValue += '-' + inputNumbersValue.substring(7, 9);
            }
            if (inputNumbersValue.length >= 10) {
                formattedInputValue += '-' + inputNumbersValue.substring(9, 11);
            }
        } else {
            formattedInputValue = '+' + inputNumbersValue.substring(0, 16);
        }
        input.value = formattedInputValue;
    }
    var onPhoneKeyDown = function (e) {
        var inputValue = e.target.value.replace(/\D/g, '');
        if (e.keyCode == 8 && inputValue.length == 1) {
            e.target.value = "";
        }
    }
    for (var phoneInput of phoneInputs) {
        phoneInput.addEventListener('keydown', onPhoneKeyDown);
        phoneInput.addEventListener('input', onPhoneInput, false);
        phoneInput.addEventListener('paste', onPhonePaste, false);
    };

    $("input#phone").keyup(function(){
        var input_phone = this;
        check_phone(input_phone);
        $('.error_phone').removeClass('visibility');
    })
    $("input#phone").change(function(){
        var input_phone = this;
        check_phone(input_phone);
        $('.error_phone').removeClass('visibility');
    })
    $('#login_table').submit(function(){
        $('.error_phone').removeClass('visibility');
        check_phone($("input#phone"));
        if ($('input#phone').hasClass('error')){
            $('.error_phone').addClass('visibility');
            return false;
        }
    });
    $('#registration_cart_form').submit(function(){
        $('.error_phone').removeClass('visibility');
        check_phone($("input#phone"));
        if ($('input#phone').hasClass('error')){
            $('.error_phone').addClass('visibility');
            return false;
        }
        if ($('#next_button').hasClass('submited')){
            return false;
        }
        $('#next_button').addClass('submited').hide();
        $('#next_button_loader').show();
    });
});
function check_phone(input_phone){
    tph = $(input_phone).val();
    tph = !tph.match(/^\+7\([0-9]{3}\)[0-9]{3}-[0-9]{2}\-[0-9]{2}/);
    $(input_phone).removeClass('success').removeClass('error');
    if (tph){
        $(input_phone).addClass('error');
    } else {
        $(input_phone).addClass('success');
    }
};
