const CASH = 0;
const NON_CASH = 1;
const MIX = 6;

let ENTER_WAS_PRESSED = false;

class AutocompleteItem {
    constructor(object) { this.id = object.id;
        this.name = object.name;
    }
    to_html(){
        return `<div class="autocomplete-item" data-id="${this.id}" data-text="${this.name.replace(/"/g, '&quot;')}" onclick="set_autocomplete(this)">${this.name}</div>`
   }
}

class AutocompleteCustomerItem extends AutocompleteItem{
    constructor(object) {
        super(object);
        this.email = object.email;
        this.phone = object.phone;
        this.sale = object.sale;
    }
    to_html() {
        return `<div class="autocomplete-customer-item"
data-sale="${this.sale}" data-email="${this.email}" data-phone="${this.phone}"
data-id="${this.id}" data-text="${this.name.replace(/"/g, '&quot;')}"
onclick="set_autocomplete_customer(this)">${this.name} - ${this.email} - ${this.phone}
</div>`
    }
}

class CartItem {
    constructor(object) {
        this.id = object.id;
        this.name = object.title;
        this.weight = object.weight;
        this.img_url = object.img_url;
        this.cost = object.cost;
        this.costField = object.costField;
        this.sale = object.sale;
        this.sale_cost = object.sale_cost;
        this.amount = object.amount;
    }

    to_html(){
        return `
<tr data-id="${this.id}">
  <td></td>             
  <td align="center px-0"><img width="50px" src="${this.img_url}"></td>
  <td>${this.name}</td>
  <td class="text-nowrap">${this.weight}</td>
  ${this.costField}
  <td class="text-nowrap px-3" align="right">${intspace(this.sale_cost.toFixed(2))} <i class="far fa-ruble-sign"></i> <br><small>${this.sale}%</small></td>
  <td class="px-3" align="center"><input class="form-control count-input" width="50" value="${intspace(this.amount)}" data-line-id="${this.id}" name="${this.id}-count"></td>
  <td class="text-nowrap px-3" align="right">${intspace(parseInt(this.cost) * parseInt(this.amount))} <i class="far fa-ruble-sign"></i></td>
  <td class="text-nowrap px-3" align="right">${intspace((this.sale_cost * parseInt(this.amount)).toFixed(2))} <i class="far fa-ruble-sign"></i></td>

  <td><button class="btn btn-danger" onclick="remove_from_cart(${this.id})"><i class="fas fa-trash"></i></button></td>
</tr>`
    }
}


function set_autocomplete(element){
    let id = $(element).attr('data-id');
    let text = $(element).attr('data-text');
    $("#product-name").val(text);
    $("#product-name").attr('data-id', id);
    $('.autocomplete-block').empty();
}

function set_autocomplete_customer(element){
    let id = $(element).attr('data-id');
    let FIO = $(element).attr('data-text');
    let email = $(element).attr('data-email');
    let phone = $(element).attr('data-phone');
    let sale = $(element).attr('data-sale');

    $("#customer").val(FIO);
    $("#customer").attr('data-id', id);
    $("#FIO-input").val(FIO);
    $("#email-input").val(email);
    $("#phone-input").val(phone);
    $("#sale-input").val(sale);
    $("#customer-id").val(id);
    $('#f_print-input').prop('checked', false);
    $('.autocomplete-customer').empty();
    update_cart();
}

let delay_timer = null;
var delay_count_timer = null;
$("body").on('keyup', '.count-input', function () {
    clearTimeout(delay_count_timer);
    var this_input = this;
    delay_count_timer = setTimeout(function () {
        $("#add-to-cart").attr('disabled', 'disabled');
        if (add_to_cart_status){
            return ;
        }
        add_to_cart_status = true;
        let data_id = $(this_input).attr('data-line-id');
        let amount = $(this_input).val();

        var data = {
           'id': data_id,
           'cost': $('.cost-input').val(),
           'amount': amount,
           'update': 1
        };
        $.ajax({
            url: '/k/add_to_cart/',
            data: data,
            success: data =>{
                if (!data.error){
                    update_cart();
                    $("#product-name").val('');
                    $("#product-name").removeAttr('data-id');
                    $("#product-amount").val(1);
                }

            },
            complete: () =>{
                add_to_cart_status = false;
                $("#add-to-cart").removeAttr('disabled');
            }
       })
    }, 2000);

});

$("body").on('keyup', '.cost-input', function () {
    clearTimeout(delay_count_timer);
    var this_input = this;
    delay_count_timer = setTimeout(function () {
        $("#add-to-cart").attr('disabled', 'disabled');
        if (add_to_cart_status){
            return ;
        }
        add_to_cart_status = true;
        let data_id = $(this_input).attr('data-line-id');
        let cost = $(this_input).val();

        var data = {
           'id': data_id,
           'cost': cost,
           'amount': $('.count-input').val(),
           'update': 1
        };
        $.ajax({
            url: '/k/add_to_cart/',
            data: data,
            success: data =>{
                if (!data.error){
                    update_cart();
                    $("#product-name").val('');
                    $("#product-name").removeAttr('data-id');
                    $("#product-amount").val(1);
                }

            },
            complete: () =>{
                add_to_cart_status = false;
                $("#add-to-cart").removeAttr('disabled');
            }
       })
    }, 2000);

});

$("#product-name").on('keyup', ()=>{
    if ($("#product-name").val() == ""){
        $(".autocomplete-block").empty();
    }
    if ($("#product-name").val().length < 3){
        return;
    }
    clearTimeout(delay_timer);
    delay_timer = setTimeout(function () {
        $.ajax({
            url: '/k/autocomplete/',
            data: {
                "q": $("#product-name").val(),
            },
            success: data=>{
                $(".autocomplete-block").empty();
                max_items = 0;
                current_autocomplete_item_index = -1;
                if (data.length == 0){

                } else {
                    data.forEach( element => {
                        max_items++;
                        let autocomplete_item = new AutocompleteItem(element);
                        $(".autocomplete-block").append(autocomplete_item.to_html());
                    })
                    if (ENTER_WAS_PRESSED && data.length == 1){
                        select_autocomplete_item();
                        ENTER_WAS_PRESSED = false;
                    }
                }
            }
        })
    }, 500);

})

function select_autocomplete_item(){
    if (current_autocomplete_item_index == -1){
        current_autocomplete_item_index = 0;
    }
    let items = document.getElementsByClassName('autocomplete-item');
    let item = items[current_autocomplete_item_index];
    set_autocomplete(item);
    add_to_cart();
    $('#product-name').val('');
}

$("#product-name").on('keydown', event => {
    if (event.keyCode == 40){ // arrow down
        // event.preventDefault();
        // current_autocomplete_item_index++;
        // if (max_items  == current_autocomplete_item_index){
        //     current_autocomplete_item_index--;
        // }
        // $('.autocomplete-item-hover').removeClass('autocomplete-item-hover');
        // let item = document.getElementsByClassName('autocomplete-item')[current_autocomplete_item_index];
        // $(item).addClass('autocomplete-item-hover');
    } else if (event.keyCode == 38){
        // event.preventDefault();
        // current_autocomplete_item_index--;
        // if (current_autocomplete_item_index < 0){
        //     current_autocomplete_item_index = 0;
        // }
        // $('.autocomplete-item-hover').removeClass('autocomplete-item-hover');
        // let item = document.getElementsByClassName('autocomplete-item')[current_autocomplete_item_index];
        // $(item).addClass('autocomplete-item-hover');
    } else if (event.keyCode == 13){
        event.preventDefault();
        let items = document.getElementsByClassName('autocomplete-item');
        ENTER_WAS_PRESSED = true;
        if (items.length == 0){
            setTimeout(function () {
                ENTER_WAS_PRESSED = false
            }, 1500)
        }
        // select_autocomplete_item();
        // }

    }
})

function update_cart(){
    let customer_id = $("#customer-id").val();
    $.ajax({
        data: {
            'user_id': customer_id,
        },
        url: '/k/update_cart/',
        success: data => {
            let cart = $('#cart-table').length === 1
                ? $("#cart-table")
                : $('#cart-table-refund');
            cart.empty()
            Array.from(data['cart']).forEach(element =>{
                if ($('#cart-table-refund').length === 1) {
                    element.costField = `<td class="px-3" align="center"><input class="form-control cost-input" width="50" value="${intspace(element.cost)}" data-line-id="${element.id}" name="${element.id}-cost"></td>`;
                } else {
                    element.costField = `<td class="text-nowrap px-3" align="right">${intspace(element.cost)} <i class="far fa-ruble-sign"></i></td>`;
                }
                let cartItem = new CartItem(element);
                cart.append(cartItem.to_html());
            });
            cart_sum = parseInt(data['result']);
            update_sums();
            $("#cart-sum").text(intspace(data['cart_sum'].toFixed(2)));
            $("#cart-sale").text(intspace(data['sale_cost'].toFixed(2)));
            $("#cart-result").text(intspace(data['result']));
            $("#cart-cents").text(intspace(data['cents'].toFixed(2)));
        }
    })
}


$(".readonly").on('keydown', event =>{
    event.preventDefault();
})
$('#calc-input').on('input', ()=>{
    let value = $('#calc-input').val();
    let non_cash = $("#non-cash-input").val();
    non_cash = parseInt(non_cash);
    if (isNaN(non_cash)){
        non_cash = 0;
    }
    let change = parseInt(value) - (cart_sum - non_cash);
    if (change >= 0){
        $('#change').text(change);
    }
})

function update_sums(){
    let value = $('.checkbox-budget:checked').val();
    if (value == CASH || value == 3){
        $("#pay-type-inputs").hide();
        $(".calculator").show();
        $("#cash-input").val(cart_sum);
        $("#cash-input").attr('readonly', 'readonly');
        $("#non-cash-input").val(0);
        $("#non-cash-input").attr('readonly', 'readonly');
    } else if (value == NON_CASH || value == 4 || value == 5){
        $("#pay-type-inputs").hide();
        $(".calculator").hide();
        $('#change-input').val(0);
        $("#non-cash-input").val(cart_sum);
        $("#non-cash-input").attr('readonly', 'readonly');
        $("#cash-input").val(0);
        $("#cash-input").attr('readonly', 'readonly');
    } else if (value == MIX){
        $("#pay-type-inputs").show();
        $(".calculator").show();
        $("#cash-input").val('');
        $("#cash-input").removeAttr('readonly');
        $("#non-cash-input").val('');
        $("#non-cash-input").removeAttr('readonly');
    }
}

$(".checkbox-budget").on('change', ()=>{
    update_sums();
})

$("#cash-input").on('input', ()=>{
    let cash = parseInt($("#cash-input").val());
    if (isNaN(cash)){
        cash = 0
    }
    let non_cash = cart_sum - cash;
    if (non_cash < 0){
        non_cash = 0
    }
    $("#non-cash-input").val(non_cash);
    $('#calc-input').val(cash);
    $('#calc-input').trigger('input')
})

$('#non-cash-input').on('input', ()=>{
    let non_cash = parseInt($("#non-cash-input").val());
    if (isNaN(non_cash)){
        non_cash = 0
    }
    let cash = cart_sum - non_cash;
    if (cash < 0){
        cash = 0
    }
    $("#cash-input").val(cash)
    $("#calc-input").trigger('input');
})

function remove_from_cart(id){
    $.ajax({
        url: '/k/remove_from_cart/',
        data: {
            'id': id,
        },
        success: ()=>{
            update_cart();
        }
    })
}

let add_to_cart_status = false;
function add_to_cart(){
    $("#add-to-cart").attr('disabled', 'disabled')
    if (add_to_cart_status){
        return ;
    }

    add_to_cart_status = true;
    let data_id = $("#product-name").attr('data-id');
    let amount = $("#product-amount").val();

    var data = {
       'id': data_id,
       'amount': amount
    };

    $.ajax({
        url: '/k/add_to_cart/',
        data: data,
        success: data =>{
            if (!data.error){
                update_cart();
                $("#product-name").val('');
                $("#product-name").removeAttr('data-id');
                $("#product-amount").val(1);
            }

        },
        complete: () =>{
            add_to_cart_status = false;
            $("#add-to-cart").removeAttr('disabled');
        }
   })
}


$('#add-to-cart').on('click', ()=>{
   add_to_cart();
});

$('#customer').on('input', ()=>{
    if ($("#customer").val() == ""){
        $(".autocomplete-customer").empty();
    }
    $.ajax({
        url: '/k/autocomplete_customers/',
        data: {
            "q": $("#customer").val(),
        },
        success: data=>{
            $(".autocomplete-customer").empty();
            max_items = 0;
            current_autocomplete_item_index = -1;
            if (data.length == 0){

            } else {
                data.forEach( element => {
                    max_items++;
                    let autocomplete_item = new AutocompleteCustomerItem(element);
                    $(".autocomplete-customer").append(autocomplete_item.to_html());
                })

            }
        }
    })
});

function intspace(value){
    let parts = value.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return parts.join(",");
}

$(document).on('click', ()=>{
    $(".autocomplete-block").empty();
})

$(document).ready(()=>{
    if (UPDATE_CART){
        update_cart();
    }
    function generate_alert_for_pay_type(){
        return `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <strong>Не выбран способ оплаты</strong>
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
        </div>
        `
    }
    function generate_alert_for_not_equal_sums(cash_val, non_cash_val){
        return `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <strong>Сумма налички(${cash_val}) и безнала(${non_cash_val}) не сходится с суммой заказа(${cart_sum})</strong>
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
        </div>
        `
    }
    function generate_alert_for_submitting(){
        return `
        <div class="alert alert-success alert-dismissible fade show alert-saving" role="alert">
            <strong>Сохраняю. Пожалуйста, подождите</strong>
        </div>
        `
    }
    function save_failed(){
        $(".reserve-button").removeAttr('disabled');
        $(".save-button").removeAttr('disabled');
        $(".cancel-button").removeAttr('disabled');
        $(".alert-saving").remove();
    }
    $("#form-cart").submit(event => {
        $(".alert-wrapper").empty();
        let active_elem = $(document.activeElement);
        let reserve = false;
        if (active_elem.attr('name') == 'reserve'){
            reserve = true;
        }
        $(".cancel-button").attr('disabled', 'disabled');
        $(".alert-wrapper").append(generate_alert_for_submitting());
        $(active_elem).attr('disabled', 'disabled')
        if (!reserve){
            let cash_val = parseInt($("#cash-input").val());
            let non_cash_val = parseInt($("#non-cash-input").val());
            if (isNaN(cash_val)){
                cash_val = 0;
            }
            if (isNaN(non_cash_val)){
                non_cash_val = 0;
            }
            let pay_type = $('.checkbox-budget:checked').val();

            if (pay_type == 3 || pay_type == 4 || pay_type == 5){
                update_sums();
                cash_val = parseInt($("#cash-input").val());
                non_cash_val = parseInt($("#non-cash-input").val());
            }
            if (pay_type === undefined){
                event.preventDefault();
                save_failed();
                $(".alert-wrapper").append(generate_alert_for_pay_type());
                return;
            }

            if (cash_val + non_cash_val != cart_sum){
                event.preventDefault();
                save_failed();
                $(".alert-wrapper").append(generate_alert_for_not_equal_sums(cash_val, non_cash_val));
                return ;
            }
        }
    });
})


