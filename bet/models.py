from django.contrib.auth.models import AbstractUser
from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin
from pagseguro.signals import notificacao_recebida
from django.db import models

from .validators import CustomASCIIUsernameValidator
from .managers import ProductPurchase, VipRequestManager

# Create your models here.

class FaqTemas(models.Model):
    choice = models.CharField(max_length=100)

    def __str__(self):
        return "{}".format(self.choice)

    
class Faq(models.Model):
    pergunta = models.CharField(max_length=80)
    resposta = models.TextField(max_length=100)
    tema = models.ForeignKey(FaqTemas, on_delete=models.CASCADE)


class CustomUser(SimpleEmailConfirmationUserMixin, AbstractUser):
    email = models.EmailField(unique=True,max_length=255)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=16, blank=True)

    def __init__(self, *args, **kwargs):
        self._meta.get_field(
            'username'
        ).validators[0] = CustomASCIIUsernameValidator()

        super().__init__(*args, **kwargs)


class Produtos(models.Model):
    nome = models.CharField(max_length=50)
    preco = models.FloatField()
    preco_text = models.CharField(max_length=20)
    descricao = models.TextField(max_length=300)
    pagseguro = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class UserProdutos(models.Model):
    user = models.ForeignKey(CustomUser,
                                on_delete=models.CASCADE)
    produto = models.ForeignKey(Produtos,
                                on_delete=models.CASCADE)
    vip_expiration = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default="aguardando")
    checkout = models.CharField(max_length=36, unique=True)
    objects = ProductPurchase()

    def __str__(self):
        return "{} - {}".format(self.produto.nome, self.user.username)


class VipRequest(models.Model):
    purchase = models.ForeignKey(UserProdutos,
                                on_delete=models.CASCADE)
    added = models.BooleanField(default=False)
    objects = VipRequestManager()


class Depoimentos(models.Model):
    nome_pessoa = models.CharField(max_length=50)
    foto = models.ImageField(upload_to="depoimentos-pics/")
    video_link = models.CharField(max_length=50)
    

def update_purchase(sender, transaction, **kwargs):
    purchase = UserProdutos.objects.update_purchase(transaction)
    
    if transaction['status'] == '3' and purchase:
        VipRequest.objects.requestVip(purchase)

notificacao_recebida.connect(update_purchase)
