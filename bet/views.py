from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeForm
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from urllib.parse import urlencode

from collections import Counter
from datetime import datetime
import json
import re

from simple_email_confirmation.models import EmailAddress
from pagseguro.api import PagSeguroApiTransparent

from .forms import CreateUserForm, LoginForm, UpdateProfile
from .models import *

CONTACT_EMAIL_MESSAGE = "Email enviado por {}, através do email {}\n\n{}"

def index(request):
    depoimentos = Depoimentos.objects.all()
    products = Produtos.objects.all()
    faq_tema = FaqTemas.objects.all().first()

    context =  {
        'site': request.site,
        'faq_tema': faq_tema,
        'depoimentos': depoimentos,
        'products': products,
        'resended': request.GET.get('resended'),
        'succes_message': True,
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = CONTACT_EMAIL_MESSAGE.format(name, email, request.POST.get('message'))
        
        send_mail(subject=subject, message=message, from_email=email, recipient_list=[settings.EMAIL_HOST_USER])
        messages.success(request, 'Email de contato enviado.')

    elif request.user.is_authenticated and bool(EmailAddress.objects.filter(user__pk=request.user.pk, confirmed_at=None)):
        if not context['resended']:
            context['success_message'] = False
            for message in messages.get_messages(request):
                if "confirmation_request" in message.tags:
                    return render(request, 'bet/home/index.html', context=context)

            print("MAARAVILAH",messages.get_messages(request))
            messages.warning(request, 'Seu email não está confirmado, por favor confirme acessando link que mandamos em seu email.')
        else:
            context['success_message'] = True
            messages.warning(request, 'Link de confirmação enviado.')

    return render(request, 'bet/home/index.html', context=context)

def faq_view(request, tema_pk):
    perguntas = Faq.objects.filter(tema__pk=tema_pk).values('pergunta', 'resposta')
    temas = FaqTemas.objects.annotate(number_of_questions=Count('faq'))

    return render(request, 'bet/faq/faq-perguntas.html', {
        'perguntas': perguntas,
        'temas': temas,
        'id': tema_pk,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('bet:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST.get('inputEmail')
            password = request.POST.get('inputPassword')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if not request.GET.get('next'):
                    return redirect('bet:profile', page="infos")
                else:
                    return HttpResponseRedirect(request.GET.get('next'))
            else:
                messages.info(request, "usuário/email ou senha incorretos")

    form = LoginForm(auto_id="%s")
    return render(request, 'bet/accounts/login.html', context={'form':form})

def logout_view(request):
    logout(request)
    return redirect('bet:index')

def register(request):
    if request.user.is_authenticated:
        return redirect('bet:index')

    form = CreateUserForm()
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            send_confirmation_link(user, request.site)

            return redirect('bet:login')
        else:
            for msgs in form.errors.as_data().values():
                for msg in msgs:
                    messages.error(request, *msg)

    return render(request, 'bet/accounts/register.html', {'form': form})

def change_pass(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)

    if form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        messages.success(request,"Senha alterada.")
    else:
        errors = json.loads(form.errors.as_json())
        
        for error_field, error_list in errors.items():
            code = error_list[0]['code']
            if code == 'password_mismatch':
                messages.error(request,'Senhas não coincidem')
            elif code == 'password_incorrect':
                messages.error(request,'Senha atual incorreta.')
            else:
                messages.error(request,error_list[0]['message'])

def change_infos(request):
    old_email = request.user.email
    form = UpdateProfile(request.POST, instance=request.user)

    if form.is_valid():
        form.save()

        if old_email != request.POST.get('email'):
            EmailAddress.objects.filter(user=request.user).delete()
            send_confirmation_link(request.user, request.site)

            messages.success(request, "Alterado com sucesso! Confirme seu email por meio do link que mandamos.")
        else:
            messages.success(request, "Alterado com sucesso!")

    else:
        errors = json.loads(form.errors.as_json())
        print(errors)
        for error in errors.values():
            message = error[0]['message']
            if 'This email address is already in use' in message:
                message = "Esse email já está cadastrado."

            messages.error(request, message)

@login_required(login_url="bet:login")
def profile_view(request, page):
    context = {
        'page': page,
        'has_vip': UserProdutos.objects.filter(user=request.user, vip_expiration__gte=datetime.now()).count(),
    }
    
    if page == "infos":
        context['form'] = UpdateProfile()

    elif page == "planos":
        try:
            context['expiration'] = UserProdutos.objects.filter(user=request.user).order_by('vip_expiration').last().vip_expiration.date()
        except AttributeError:
            context['expiration'] = "Não contratado"

    if request.method == 'POST':
        if page == "password":
            change_pass(request)

        elif page == "infos":
            change_infos(request)
            return redirect("bet:profile", page="infos")

    return render(request, "bet/accounts/profile-%s.html"%(page), context=context)

@login_required(login_url="bet:login")
def request_vip(request):
    purchase = UserProdutos.objects.filter(user=request.user, vip_expiration__gte=datetime.now(), status="pago").order_by('vip_expiration').last()

    if purchase:
        vip_req = VipRequest.objects.requestVip(purchase)
        vip_req.added = False
        vip_req.save()

        messages.success(request, "Já solicitamos a sua entrada ao grupo, iremos verificar os dados.")

    else:
        messages.warning(request, "Você não possui esse plano. Gostaria de contratar? ")

    return redirect("bet:profile", page="planos")

@login_required(login_url="bet:login")
def request_curso(request):
    has_course = UserProdutos.objects.filter(user=request.user, produto__pk=2, status="pago").count()

    if has_course:
        message = "Olá {}, aqui está o link do nosso curso.\n\n{}\n\nTenha um bom aprendizado!\n atenciosamente hackeandoabanca.".format(request.user.first_name,"https://google.com")
        send_mail(subject="Solicitação do link do curso", message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=[request.user.email])

        messages.success(request, "Enviamos o link para o seu email.")

    else:
        messages.warning(request, "Você não possui esse plano. Gostaria de contratar? ")

    return redirect("bet:profile", page="planos")

@login_required(login_url="bet:login")
def pagamento_page(request, product_pk):
    
    if not bool(EmailAddress.objects.filter(user__pk=request.user.pk, confirmed_at=None)):
        produto = Produtos.objects.get(pk=product_pk)

        if request.method == 'POST':
            data = UserProdutos.objects.create_checkout(request, produto)
            print("DATA")
            print(data)
            if data['status_code'] != 200:
                messages.warning(request, "Existem campos inválidos. Por favor tente novamente")
                return redirect("bet:pagamento", product_pk=product_pk)
            try:
                link_boleto = data['transaction']['paymentLink']
                message = "Olá {}, aqui está o boleto para o pagamento do plano.\nAgradecemos sua compra. {}".format(
                    request.user.first_name, request.site.name)
                send_mail("Boleto de pagamento", message, from_email=settings.EMAIL_HOST_USER, recipient_list=[request.user.email,])

            except KeyError:
                pass

            messages.success(request, 'Obrigado por comprar um de nossos planos, enviaremos um email quando o pagamento for confirmado.')
                        
        else:
                context = {
                    'nome': produto.nome,
                    'preco': ("%.2f"%produto.preco).replace('.',',')
                }
                return render(request, "bet/home/pagamento.html", context=context)
    else:
        messages.warning(request, 'Por favor confirme seu email antes de comprar um dos nossos Planos.', extra_tags="confirmation_request")

    return redirect( "bet:index")

@login_required(login_url="bet:login")
def sessionID(request):
    data = PagSeguroApiTransparent().get_session_id()
    return JsonResponse(data)

def send_confirmation_link(user, site):
    _email = user.email
    confirmation_key = user.add_unconfirmed_email(_email)
    message = render_to_string("bet/emails/confirmation_email.txt", context= {
        'nome': user.first_name, 
        'id': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': confirmation_key,
        'protocol': 'https',
        'domain': site
    })

    send_mail('Confirmação de conta', message, settings.EMAIL_HOST_USER, [_email])

def resend_link_confirmation(request):
    if request.user.is_authenticated and not request.user.is_confirmed:
        EmailAddress.objects.filter(user=request.user).delete()

        send_confirmation_link(request.user, request.site)

        base_url = reverse('bet:index')
        query_string =  urlencode({'resended': True})
        url = '{}?{}'.format(base_url, query_string)

        return redirect(url)

    else:
        return redirect('bet:index')

def email_confirmation(request, uidb64, token):
    pk = force_text(urlsafe_base64_decode(uidb64))
    user = CustomUser.objects.get(pk=pk)

    try:
        user.confirm_email(token)
        if user.is_confirmed:
            context = {
                'link': 'bet:index',
                'link_text': 'Home',
                'titulo': "Parabéns! Sua conta foi ativada.",
                'info': 'Volte para home e adquira um dos nossos planos!'
            }
            return render(request, "bet/accounts/account_activation.html", context=context)
        else:
            raise EmailAddress.DoesNotExist
    except EmailAddress.DoesNotExist:
        context = {
                'link': 'bet:resend-confirmation',
                'link_text': 'Resend link',
                'titulo': "Oops! Algo não deu certo.",
                'info': 'Talvez o link tenha expirado, gostarira de outro?'
            }
        return render(request, "bet/accounts/account_activation.html", context=context)