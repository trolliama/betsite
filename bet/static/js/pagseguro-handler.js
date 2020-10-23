var base_url = "https://"+window.location.hostname+"/pagamento/"
var objs_parcelas;
var brand;
var success = false;


$.ajax({
    url: base_url+"session-id",
    dataType: 'json',
    success: function(response){
        PagSeguroDirectPayment.setSessionId(response['session_id']);
    },
    error: function(response){
        console.log(response);
    }
});

function getBrand(campo){
    var numero = campo.val().replace(/\D/g, '');
    if (numero.length >= 6){
        numero = numero.slice(0,6);
        console.log('numero');
        console.log(numero);
        PagSeguroDirectPayment.getBrand({
            cardBin: numero,
            success: function(response) {
              brand = response['brand']['name'];
              var amount = parseFloat($("#item-price").val());

              getInstallment(amount, brand);
            },
            error: function(response) {
              console.log(response);
            }
        });
    }
}

function getInstallment(amount, brand){
    PagSeguroDirectPayment.getInstallments({
        amount: amount,
        maxInstallmentNoInterest: 0,
        brand: brand,
        success: function(response){
            $.each(response['installments'], function (key, val) {
                var options = '';
                objs_parcelas = val;

                $.each(val, function(i, obj_val){
                    options += '<option value="' + obj_val.quantity + '">' + obj_val.quantity + '</option>';
                });
                
                $("#parcelas").html(options);
                $("#parcelas").trigger("change");
            });
       },
        error: function(response) {
            console.log(response);
       }
    });
}

function getCardToken(card_num, cvv, month_exp, year_exp){
    PagSeguroDirectPayment.createCardToken({
        cardNumber: card_num, // Número do cartão de crédito
        brand: brand, // Bandeira do cartão
        cvv: cvv, // CVV do cartão
        expirationMonth: month_exp, // Mês da expiração do cartão
        expirationYear: year_exp, // Ano da expiração do cartão, é necessário os 4 dígitos.
        success: function(response) {
            $("#card-token").val(response['card']['token']);
            var names_id = new Array("number", "cvv", "expiration");
            console.log('si');
            $("#pagamento-invalido").hide();
            for (var i = 0; i < names_id.length; i++){
                $("#cc-"+names_id[i]).addClass("is-valid");
                $("#cc-"+names_id[i]).removeClass("is-invalid");
                $("#cc-"+names_id[i]).siblings('.invalid-feedback').hide();
            }
            $("form").trigger("submit");
        },
        error: function(response) {
            console.log('no');
            var names_id = new Array("number", "cvv", "expiration");
            
            $("#pagamento-invalido").show();
            for (var i = 0; i < names_id.length; i++){
                $("#cc-"+names_id[i]).addClass("is-invalid");
                $("#cc-"+names_id[i]).removeClass("is-valid");
                $("#cc-"+names_id[i]).siblings('.invalid-feedback').show();
            }
            $("form").trigger("submit");
        },
      });
}

function getSenderHash(){
    PagSeguroDirectPayment.onSenderHashReady(function(response){
        if(response.status == 'error') {
        // $("#sender-hash").val(""); //Hash estará disponível nesta variável.
        console.log(response.message);
        }
        $("#sender-hash").val(response.senderHash); //Hash estará disponível nesta variável.
        console.log("sender-hash")
        $("form").trigger("submit");
      });
}

