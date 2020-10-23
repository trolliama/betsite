from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django import forms
from .models import CustomUser

class CreateUserForm(UserCreationForm):
    error_messages = {
        'password_mismatch': "Senhas não coincidem",
    }
    phone = forms.CharField(max_length=16)

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        campos = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'phone']
        
        for campo in campos:
            self.fields[campo].widget.attrs['class'] = 'form-control'
            self.fields[campo].widget.attrs['id'] = 'input'+campo.capitalize()
        
        self.fields['first_name'].widget.attrs['autofocus'] = 'autofocus'

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'phone']
        error_messages = {
            'username':{
                'unique': 'Esse usuário já existe.',
            },
            'email':{
                'unique': 'Esse email já existe.'
            }
        }

class LoginForm(forms.Form):
    widgets = {
        'email': forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Email address',
            'name': 'username',
            'autofocus':True,
        }),
        'password': forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'Senha',
            'name': 'password',
        }),
    }

    inputEmail = forms.CharField(label="User/Email", widget=widgets['email'])
    inputPassword = forms.CharField(label="Senha", widget=widgets['password'])
    

class UpdateProfile(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone')
        error_messages = {
            'username':{
                'unique': 'Esse usuário já existe.',
            },
            'email':{
                'unique': 'Esse email já existe.'
            }
        }

        
    def clean_email(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        if email and CustomUser.objects.filter(email=email).exclude(username=self.instance.username).count():
            raise forms.ValidationError('This email address is already in use. Please supply a different email address.')

        return email