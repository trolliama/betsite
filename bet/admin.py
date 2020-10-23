from django.contrib import admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject

from .models import *


def make_added(modeladmin, request, queryset):
    queryset.update(added=True)

def remove_added(modeladmin, request, queryset):
    queryset.update(added=False)

def send_email_telegram(modeladmin, request, queryset):
    for query in queryset:
        message = render_to_string('bet/emails/requisicao_numero.txt', {'nome': query.purchase.user.first_name,
                                                                        'site': SimpleLazyObject(lambda: get_current_site(request))})

        send_mail(subject="Número do telegram", message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=[query.purchase.user.email])

remove_added.short_description = "Marcar como não adicionados"
make_added.short_description = "Marcar como adicionados"
send_email_telegram.short_description = "Requisitar usuário/número telegram."

# Register your models here.
@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('pergunta', 'tema')

@admin.register(FaqTemas)
class FaqTemasAdmin(admin.ModelAdmin):
    list_display = ('choice',)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username','email','first_name','last_name')

@admin.register(Produtos)
class ProdutosAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'preco_text', 'descricao', 'pagseguro')

@admin.register(UserProdutos)
class UserProdutosAdmin(admin.ModelAdmin):
    list_display = ('user','produto','vip_expiration','checkout','status')

@admin.register(VipRequest)
class VipRequestAdmin(admin.ModelAdmin):
    date_hierarchy = "purchase__vip_expiration"
    empty_value_display = '???'
    list_display = ('get_phone','get_expiration','added',)
    list_filter = ('added',('purchase__vip_expiration', DateTimeRangeFilter),)
    actions = [make_added, remove_added, send_email_telegram]

    def get_phone(self, obj):
        return obj.purchase.user.phone

    def get_expiration(self, obj):
        return obj.purchase.vip_expiration 

    get_phone.short_description = "Celular"
    get_phone.admin_order_field = 'purchase__user__phone'

    get_expiration.short_description = "Expiração"
    get_expiration.admin_order_field = '-purchase__vip_expiration'

@admin.register(Depoimentos)
class DepoimentosAdmin(admin.ModelAdmin):
    list_display = ('nome_pessoa','foto','video_link')