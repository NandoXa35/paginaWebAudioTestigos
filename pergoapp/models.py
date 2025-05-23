from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Radio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="radio")
    nombre_radio = models.CharField(max_length=100,unique=True)
    siglas = models.CharField(max_length=20, unique=True)
    correo_electronico = models.EmailField()
    estado = models.CharField(max_length=100)
    software = models.IntegerField(default=0)
    estado_suscripcion = models.CharField(
        max_length=20,
        choices=[("Activo", "Activo"), ("Inactivo", "Inactivo"),("Cancelado", "Cancelado")],  #Cancelado
        default="Inactivo"
    )
    fecha_inicio = models.DateField(default=timezone.now)
    dias_restantes = models.IntegerField(default=0)

    # PayPal
    paypal_subscription_id = models.CharField(max_length=64, null=True, blank=True)
    paypal_custom_id = models.CharField(max_length=127, null=True, blank=True)  # Nuevo campo


    def __str__(self) -> str:
        return self.siglas