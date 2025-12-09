from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PasswordStrengthValidator:
    """
    Validador 100% compatible con Django 6.0 AUTH_PASSWORD_VALIDATORS.
    """
    def __init__(self):
        self.help_text = _(
            "Tu contraseña debe tener al menos 8 caracteres, una mayúscula y un número."
        )

    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("La contraseña debe tener al menos 8 caracteres."),
                code='password_too_short'
            )
        
        if not any(c.isupper() for c in password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper'
            )
        
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_digit'
            )

    def get_help_text(self):
        return self.help_text