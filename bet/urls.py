from django.urls import path

from . import views

app_name = 'bet'

urlpatterns = [
    path('', views.index, name='index'),
    path('faq/<int:tema_pk>', views.faq_view, name='faq'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/<page>', views.profile_view, name="profile"),
    path('request/vip', views.request_vip, name="request-vip"),

    path('email/confirmation/<uidb64>/<token>', views.email_confirmation, name='email-confirmation'),
    path('email/resend/link/', views.resend_link_confirmation, name='resend-confirmation'),

    path('pagamento/<int:product_pk>', views.pagamento_page, name="pagamento"),
    path('pagamento/session-id', views.sessionID, name='pagseguro-session-id'),
]