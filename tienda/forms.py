from django import forms
from django.contrib.auth.models import User
from .models import Producto, Categoria
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    """Formulario de login personalizado (sin AuthenticationForm)"""
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


class RegistroForm(UserCreationForm):
    """
    Formulario de registro con:
    - Nombre completo
    - Email obligatorio
    - Validación automática de contraseña (por AUTH_PASSWORD_VALIDATORS)
    """
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
        help_text="Tu nombre y apellido"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        help_text="Usaremos este correo para recuperar tu contraseña"
    )

    class Meta:
        model = User
        fields = ("nombre", "username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mejorar textos de ayuda
        self.fields['password1'].help_text = "Mínimo 8 caracteres, 1 mayúscula y 1 número."
        self.fields['password2'].help_text = "Repite la contraseña para verificar."

    def save(self, commit=True):
        user = super().save(commit=False)
        # Separar nombre y apellido
        nombre_completo = self.cleaned_data['nombre'].strip()
        partes = nombre_completo.split(' ', 1)
        user.first_name = partes[0]
        user.last_name = partes[1] if len(partes) > 1 else ''
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

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