from django.contrib.auth.password_validation import UserAttributeSimilarityValidator
from django.contrib.auth.password_validation import MinimumLengthValidator
from django.contrib.auth.password_validation import CommonPasswordValidator
from django.contrib.auth.password_validation import NumericPasswordValidator

from django.contrib.auth.validators import ASCIIUsernameValidator

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _, ngettext


class CustomASCIIUsernameValidator(ASCIIUsernameValidator):
    regex = r'^[\w.@+-]+\Z'
    message = _(
        'Usuário só pode conter letras, '
        'números, e \/@/./+/-/_ caracteres.'
    )


class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as error:
            verbose_name = error.messages[0].split()[-1]
            if 'username' in verbose_name:
                verbose_name = 'usuário.'

            elif 'name' in verbose_name:
                verbose_name = 'nome ou sobrenome.'

            raise ValidationError(
                        _("A senha é muito parecida com o campo %(verbose_name)s"),
                        code='password_too_similar',
                        params={'verbose_name':verbose_name})

    def get_help_text(self):
        return _("Sua senha não pode ser similar a outros dados pessoais.")


class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(
                ngettext(
                    "Essa senha é muito pequena. Deve conter pelo menos %(min_length)d caracter.",
                    "Essa senha é muito pequena. Deve conter pelo menos %(min_length)d caracteres.",
                    self.min_length
                ),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return ngettext(
            "Sua senha deve conter pelo menos %(min_length)d caracter.",
            "Sua senha deve conter pelo menos %(min_length)d caracteres.",
            self.min_length
        ) % {'min_length': self.min_length}


class CustomCommonPasswordValidator(CommonPasswordValidator):
    
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(
                _("Essa senha é muito comum."),
                code='password_too_common',
            )

    def get_help_text(self):
        return _("Sua senha não pode ser uma senha comum, tente usar caracteres especiais.")


class CustomNumericPasswordValidator(NumericPasswordValidator):

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(
                _("A senha não pode conter apenas números."),
                code='password_entirely_numeric',
            )

    def get_help_text(self):
        return _("Sua senha não pode ter apenas números.")
