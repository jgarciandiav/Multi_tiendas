# tienda/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_password_strength(value):
    """
    Valida que la contraseña tenga:
    - Mínimo 8 caracteres
    - Al menos 1 mayúscula
    - Al menos 1 número
    """
    if len(value) < 8:
        raise ValidationError(
            _("La contraseña debe tener al menos 8 caracteres."),
            code='password_too_short'
        )
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError(
            _("La contraseña debe contener al menos una letra mayúscula."),
            code='password_no_upper'
        )
    
    if not re.search(r'[0-9]', value):
        raise ValidationError(
            _("La contraseña debe contener al menos un número."),
            code='password_no_digit'
        )