from rest_framework import serializers
from django.contrib.auth.models import User

from pergoapp.models import Radio


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class InfoRadioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Radio
        fields = ['nombre_radio', 'siglas', 'estado','estado_suscripcion', 'fecha_inicio', 'dias_restantes']


class SuscripcionSerializer(serializers.Serializer):
    """Solicitud: solo le llega el ID de la radio."""
    radio_id = serializers.IntegerField()
