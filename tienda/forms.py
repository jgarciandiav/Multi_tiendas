from django import forms
from django.contrib.auth.models import User
from .models import Producto, Categoria
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from tienda.validators import PasswordStrengthValidator
from django.core.exceptions import ValidationError

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )


class RegistroForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'})
    )
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        help_text="Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 carácter especial (@, #, $, %, &)."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar Contraseña'})
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise forms.ValidationError("Este campo es obligatorio.")
        validator = PasswordStrengthValidator()
        validator.validate(password)  # Lanza ValidationError si falla
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        return cleaned_data
        
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'cantidad', 'categoria', 'fecha_vencimiento', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()  # ← Impide seleccionar fechas pasadas en el input
            }),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(padre__isnull=False)

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha and fecha < timezone.now().date():
            raise forms.ValidationError("La fecha de vencimiento no puede ser anterior al día de hoy.")
        return fecha
    
# tienda/forms.py (añade al final)

class AdminCrearUsuarioForm(forms.Form):
    """
    Formulario para que el administrador cree usuarios con validación reforzada.
    """
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 carácter especial (@#$%&*)."
    )
    rol = forms.ChoiceField(
        choices=[('Administrador', 'Administrador'), ('Almacenero', 'Almacenero')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Validar con nuestro validador
        validator = PasswordStrengthValidator()
        try:
            validator.validate(password)
        except ValidationError as e:
            raise forms.ValidationError(e.message)
        return password    