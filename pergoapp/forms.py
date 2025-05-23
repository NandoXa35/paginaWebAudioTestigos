# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Radio

# Tus listas de estados y automatizadores:
ESTADOS = [
    ('', '---------'),
    ('Aguascalientes', 'Aguascalientes'),
    ('Baja California', 'Baja California'),
    ('Baja California Sur', 'Baja California Sur'),
    ('Campeche', 'Campeche'),
    ('Chiapas', 'Chiapas'),
    ('Chihuahua', 'Chihuahua'),
    ('Coahuila', 'Coahuila'),
    ('Colima', 'Colima'),
    ('Durango', 'Durango'),
    ('Guanajuato', 'Guanajuato'),
    ('Guerrero', 'Guerrero'),
    ('Hidalgo', 'Hidalgo'),
    ('Jalisco', 'Jalisco'),
    ('México', 'México'),
    ('Michoacán', 'Michoacán'),
    ('Morelos', 'Morelos'),
    ('Nayarit', 'Nayarit'),
    ('Nuevo León', 'Nuevo León'),
    ('Oaxaca', 'Oaxaca'),
    ('Puebla', 'Puebla'),
    ('Querétaro', 'Querétaro'),
    ('Quintana Roo', 'Quintana Roo'),
    ('San Luis Potosí', 'San Luis Potosí'),
    ('Sinaloa', 'Sinaloa'),
    ('Sonora', 'Sonora'),
    ('Tabasco', 'Tabasco'),
    ('Tamaulipas', 'Tamaulipas'),
    ('Tlaxcala', 'Tlaxcala'),
    ('Veracruz', 'Veracruz'),
    ('Yucatán', 'Yucatán'),
    ('Zacatecas', 'Zacatecas'),
]


class UserAndRadioCreationForm(UserCreationForm):
    """
    Formulario que combina la creación de usuario con los datos
    de la Radio (nombre, siglas, email, etc.).
    """
    nombre_radio = forms.CharField(label='Nombre de la Radio')
    siglas = forms.CharField(label='Siglas')
    correo_electronico = forms.EmailField(label='Correo electrónico')
    estado = forms.ChoiceField(choices=ESTADOS, label='Estado')

    class Meta(UserCreationForm.Meta):
        # Reutiliza el modelo User por defecto de Django
        model = User
        fields = ['username', 'password1', 'password2']
        # También podrías agregar aquí si deseas más campos de User,
        # como 'email', 'first_name', etc.
