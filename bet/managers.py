from django.db.models import Manager
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string

from pagseguro.api import PagSeguroItem, PagSeguroApiTransparent

from datetime import datetime
from dateutil.relativedelta import relativedelta

import re

class ProductPurchase(Manager):

    def clean_sender(self, request):
        return {
            'name':request.POST.get('firstName') + " " + request.POST.get("lastName"),
            'area_code':request.POST.get('celular')[1:3],
            'phone':request.POST.get('celular')[4:].replace('-','').strip(),
            'email': request.user.email,
            'cpf':"".join(re.findall(r'\d+',request.POST.get('cpf'))),
        }

    def clean_shipping_billing(self, request):
        return {
            'street': request.POST.get('rua'),
            'number': int(request.POST.get('numero')),
            'complement': request.POST.get('complemento'),
            'district': request.POST.get('bairro'),
            'postal_code': "".join(re.findall(r'\d+',request.POST.get('cep'))),
            'city': request.POST.get('cidade'),
            'state': request.POST.get('estado'),
            'country': 'BRA',
        }

    def create_purchase(self, request, produto, checkout):
        self.create(user=request.user, produto=produto, checkout=checkout)

    def create_checkout(self, request, produto):
        api = PagSeguroApiTransparent(reference=produto.pk)
        
        sender = self.clean_sender(request)
        api.set_sender(**sender)

        shipping_billing = self.clean_shipping_billing(request)
        api.set_shipping(**shipping_billing)

        
        payment_method = request.POST.get('paymentMethod')

        api.set_sender_hash(request.POST.get('sender-hash'))
        api.set_payment_method(payment_method)

        if payment_method == 'creditcard':
            data = {'quantity': request.POST.get('parcelas'), 'value': request.POST.get('value-parcelas'), 'name': sender['name'], 'birth_date': '27/10/1987', 'cpf': sender['cpf'], 'area_code': sender['area_code'], 'phone': sender['phone'],}
            api.set_creditcard_data(**data)
            api.set_creditcard_billing_address(**shipping_billing)
            api.set_creditcard_token(request.POST.get('card-token'))
        
        item = PagSeguroItem(id=produto.pk, description=produto.descricao, amount="%.2f"%produto.preco, quantity=1)
        api.add_item(item)
        
        data = api.checkout()

        if data['status_code'] == 200:
            self.create_purchase(request, produto, data['code'])

        return data

    def update_purchase(self, transaction):
        status_map = {
            '3': 'pago',
            '7': 'cancelado'
        }

        purchase = self.filter(checkout=transaction['code']).first()
        if not purchase:
            return
        if transaction['status'] not in ('3', '7'):
            return purchase

        purchase.status = status_map[transaction['status']]
        purchase.save()

        if transaction['status'] == '3':
            last_purchases = self.filter(user=purchase.user, status="pago").exclude(checkout=transaction['code']).order_by('vip_expiration')
            try:
                last_expiration = last_purchases.last().vip_expiration.date()
            except AttributeError:
                last_expiration = datetime.today().date()
            self.updateExpiration(purchase, last_expiration)

        self.sendMail(purchase, transaction['status'])

        return purchase

    def updateExpiration(self, purchase, last_expiration):
        expirations = {
            1: 30,
            2: 7,
            3: 90,
        }
        
        try:
            if last_expiration <= datetime.today().date():
                purchase.vip_expiration = datetime.today() + relativedelta(days=expirations[purchase.produto.pk])
            else:
                purchase.vip_expiration = last_expiration + relativedelta(days=expirations[purchase.produto.pk])

            purchase.save()

        except Exception as e:
            print(e)

    def sendMail(self, purchase, stts):
        confirmed_subject = render_to_string('bet/email/buy_confirmed_subject.txt')
        canceled_subject = render_to_string('bet/email/cancel_subject.txt')

        if stts == "3":
            if purchase.produto.pk != 2:
                message = render_to_string('bet/emails/vip_email.txt', {'nome': purchase.produto.nome})
            else:
                message = render_to_string('bet/emails/curso_email.txt',{'nome': purchase.produto.nome})
            
            send_mail(subject=confirmed_subject, message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=[purchase.user.email])
            
        else:
            message = render_to_string('bet/emails/cancel_email.txt', {'plano': purchase.produto.nome, 'nome': purchase.user.first_name})
            send_mail(subject=canceled_subject, message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=[purchase.user.email])


class VipRequestManager(Manager):

    def requestVip(self, purchase):
        old_request = self.filter(purchase__user=purchase.user).first()

        if old_request:
            old_request.purchase = purchase
            old_request.save()

            return old_request
        
        return self.create(purchase=purchase)