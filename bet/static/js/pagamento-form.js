// Example starter JavaScript for disabling form submissions if there are invalid fields

$("#credit-items").hide();

$("#parcelas").change(function(){
  $("#credit-items").show();

  var parcela = $(this).val();
  var amount = "R$"+objs_parcelas[parcela - 1]['installmentAmount'].toFixed(2);
  var total = "R$"+ objs_parcelas[parcela - 1]['totalAmount'].toFixed(2);

  var parcela_text = parcela + "x";
  $("#item-parcelas").find("h6").text(parcela_text);
  $("#item-parcelas").find("span").text(amount.replace(".",","));

  $("#item-total").find("strong").text(total.replace(".",","));
  $("#value-parcelas").val(objs_parcelas[parcela - 1]['installmentAmount'].toFixed(2))
});

$("#cc-number").on("keyup", function(){
    getBrand($(this));
});

function testCPF(cpf){
  cpf = cpf.replace(/\D/g, '');
  var Soma;
  var Resto;
  Soma = 0;
  if (cpf == "00000000000"){
      return false;
  }
  var i;
  for (i=1; i<=9; i++) Soma = Soma + parseInt(cpf.substring(i-1, i)) * (11 - i);
  Resto = (Soma * 10) % 11;

    if ((Resto == 10) || (Resto == 11))  Resto = 0;
    if (Resto != parseInt(cpf.substring(9, 10)) ) return false;

  Soma = 0;
    for (i = 1; i <= 10; i++) Soma = Soma + parseInt(cpf.substring(i-1, i)) * (12 - i);
    Resto = (Soma * 10) % 11;

    if ((Resto == 10) || (Resto == 11))  Resto = 0;
    if (Resto != parseInt(cpf.substring(10, 11) ) ) return false;
    return true;
}

function testCNPJ(cnpj) {
 
  cnpj = cnpj.replace(/[^\d]+/g,'');

  if(cnpj == '') return false;
   
  if (cnpj.length != 14)
      return false;

  // Elimina CNPJs invalidos conhecidos
  if (cnpj == "00000000000000" || 
      cnpj == "11111111111111" || 
      cnpj == "22222222222222" || 
      cnpj == "33333333333333" || 
      cnpj == "44444444444444" || 
      cnpj == "55555555555555" || 
      cnpj == "66666666666666" || 
      cnpj == "77777777777777" || 
      cnpj == "88888888888888" || 
      cnpj == "99999999999999")
      return false;
       
  // Valida DVs
  tamanho = cnpj.length - 2
  numeros = cnpj.substring(0,tamanho);
  digitos = cnpj.substring(tamanho);
  soma = 0;
  pos = tamanho - 7;
  for (i = tamanho; i >= 1; i--) {
    soma += numeros.charAt(tamanho - i) * pos--;
    if (pos < 2)
          pos = 9;
  }
  resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
  if (resultado != digitos.charAt(0))
      return false;
       
  tamanho = tamanho + 1;
  numeros = cnpj.substring(0,tamanho);
  soma = 0;
  pos = tamanho - 7;
  for (i = tamanho; i >= 1; i--) {
    soma += numeros.charAt(tamanho - i) * pos--;
    if (pos < 2)
          pos = 9;
  }
  resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
  if (resultado != digitos.charAt(1))
        return false;
         
  return true;
  
}

function addClasses(campo, result){
  if(!result){
    campo.removeClass('is-valid');
    campo.addClass('is-invalid');
    campo.siblings('.invalid-feedback').show();
  }
  else{
    campo.removeClass('is-invalid');
    campo.addClass('is-valid');
    campo.siblings('.invalid-feedback').hide();
  }
}

// ----- CEP ------------
function limpa_formulário_cep() {
    //Limpa valores do formulário de cep.
    document.getElementById('rua').value=("");
    document.getElementById('bairro').value=("");
    document.getElementById('estado').value=("");
    $("#estado").trigger("change");
    document.getElementById('cidade').value=("");
}

function pesquisacep(valor, campo_cep) {

//Nova variável "cep" somente com dígitos.
var cep = valor.replace(/\D/g, '');

//Verifica se campo cep possui valor informado.
if (cep != "") {
    console.log('ofh');
    console.log(cep);
    //Expressão regular para validar o CEP.
    var validacep = /^[0-9]{8}$/;

    //Valida o formato do CEP.
    if(validacep.test(cep)) {
        document.getElementById('rua').value="...";
        document.getElementById('bairro').value="...";
        document.getElementById('estado').value="...";
        $("#estado").trigger("change");
        document.getElementById('cidade').value

        $.ajax({
          url: 'https://viacep.com.br/ws/'+cep+'/json/unicode/',
          dataType: 'json',
          success: function(resposta){
            if(!("erro" in resposta)){
              document.getElementById('rua').value=(resposta.logradouro);
              document.getElementById('bairro').value=(resposta.bairro);
              document.getElementById('estado').value=(resposta.uf);
              $("#estado").trigger("change");
              document.getElementById('cidade').value=(resposta.localidade);
            
              addClasses(campo_cep, true);
            }
            else{
              limpa_formulário_cep();
              addClasses(campo_cep, false);
            }
          }
        });

    } //end if.
    else {
        //cep é inválido.
        limpa_formulário_cep();
        addClasses(campo_cep, false);

    }
} //end if.
else {
  console.log('kk');
    //cep sem valor, limpa formulário.
    limpa_formulário_cep();
    addClasses(campo_cep, false);

}
};

$(document).ready(function() {
  $("form").submit(function(e){
    $("#cpf").trigger("blur");

    var cpf_invalid = document.getElementById("cpf").classList.contains("is-invalid");
    var cep_invalid = document.getElementById("cep").classList.contains("is-invalid");

    var form = $(this)[0];

    if (form.checkValidity() === false | cpf_invalid | cep_invalid) {
      $("#cep").trigger("blur");
      console.log("VAGABUNDA")
      e.preventDefault();
      e.stopPropagation();
    }
    else if($("#card-token").val() === "" | $("#sender-hash").val() === ""){
      console.log("VAGABUNDA 2")
      e.preventDefault();
      e.stopPropagation();
    }
    $(this).addClass('was-validated');
  });
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function submitForm(){
  
  if ($("#credit").prop("checked")) {
    console.log("ENTRANNNNN")
    var card_num = parseInt($("#cc-number").val().replace(/\D/g,''));
    var cvv = parseInt($("#cc-cvv").val());
    var exp = $("#cc-expiration").val().split("/");
    var month_exp = parseInt(exp[0]);
    var year_exp = parseInt(exp[1]);

    getCardToken(card_num, cvv, month_exp, year_exp);
  }
  else{
    $("#card-token").val("none");
  }
  getSenderHash();
}

$("#cpf").blur(function(){
  valid = ($(this).length < 15 ) ? testCPF($(this).val()) : testCNPJ($(this).val());
  addClasses($(this), valid);
});

$("#cep").blur(function(){
  pesquisacep($(this).val(), $(this));
})

$("#boleto").click(function(){
  $("#credit-card-infos").hide();
  $("#pagamento-invalido").hide()
  $("#credit-items").hide();

  $("#credit-card-infos .control-form").each(function(){
    $(this).removeAttr('required');
    addClasses($(this), true);

  })
  $("#cc-name").removeAttr('required');
  $("#parcelas").removeAttr('required');

  addClasses($("#parcelas"), true);
  addClasses($("#cc-name"), true);
})


$("#credit").click(function(){
  $("#credit-card-infos").show();
  $("#credit-card-infos .control-form").each(function(){
    $(this).attr('required','true');
    $(this).removeClass("is-valid");
  })
  $("#cc-name").attr('required','true');
  $("#cc-name").removeClass("is-valid");
  $("#parcelas").attr('required','true');
  $("#parcelas").removeClass("is-valid");


})

// --------- Estados e Cidades ----------
$(document).ready(function () {
		
  $.getJSON('../static/js/estados_cidades.json', function (data) {
    var options = '<option value="">Escolha...</option>';	

    $.each(data, function (key, val) {
      options += '<option value="' + val.sigla + '">' + val.nome + '</option>';
    });					
    $("#estado").html(options);				
    
    $("#estado").change(function () {				
    
      var options_cidades = '<option value="">Escolha...</option>';
      var str = "";					
      
      $("#estado option:selected").each(function () {
        str += $(this).text();
      });
      
      $.each(data, function (key, val) {
        if(val.nome == str) {							
          $.each(val.cidades, function (key_city, val_city) {
            options_cidades += '<option value="' + val_city + '">' + val_city + '</option>';
          });							
        }
      });

      $("#cidade").html(options_cidades);
      
    }).change();		
  
  });

  if ($("#boleto").prop("checked")) {
    $("#boleto").trigger("click");
  }
});

// --------- MASKS -----------
var options =  {
  onKeyPress: function(_doc, e, field, options) {
    var masks = ['00.000.000/0000-00', '000.000.000-000'];
    var mask = (_doc.replace(/\D/g, '').length>11) ? masks[0] : masks[1];
    $('#cpf').mask(mask, options);
}};

$('#cep').mask('00000-000');
$('#cpf').mask('000.000.000-000', options);
$('#celular').mask('(00) 00000-0000');
$("#numero").mask('000');
$("#cc-expiration").mask('00/0000');
$("#cc-cvv").mask('000');
$("#cc-number").mask('0000 0000 0000 0000');