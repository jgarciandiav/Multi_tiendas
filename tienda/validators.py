# tienda/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PasswordStrengthValidator:
    """
    Validador robusto para contraseñas:
    - 8+ caracteres
    - 1 mayúscula
    - 1 número
    - 1 carácter especial
    """
    def __init__(self):
        self.help_text = _(
            "La contraseña debe tener al menos 8 caracteres, una mayúscula, un número y un carácter especial (@#$%&*)."
        )

    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("La contraseña debe tener al menos 8 caracteres."),
                code='password_too_short'
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper'
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_digit'
            )
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un carácter especial (@, #, $, %, &, *, etc.)."),
                code='password_no_special'
            )

    def get_help_text(self):
        return self.help_text