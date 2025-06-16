import datetime
from django.utils import timezone
from datetime import timedelta
from .models import Radio

from django.utils import timezone
import requests
from django.utils import timezone

# ─────────────────────────── util ────────────────────────────
def hay_campanas(bucket_name: str, usuario: str) -> bool:
    """
    Devuelve True si en gs://<bucket>/<usuario>/Campañas/ existe
    al menos un objeto distinto de '.placeholder'.
    """
    client = storage.Client()
    blobs  = client.list_blobs(bucket_name, prefix=f"{usuario}/Campañas/")

    for blob in blobs:                       # recorre todo el prefijo
        nombre = os.path.basename(blob.name)
        if nombre and nombre != '.placeholder':
            return True                      # hay algo real
    return False                              # solo placeholder o vacío

def consultar_estado_paypal(subscription_id, access_token):
    url = f"https://api-m.paypal.com/v1/billing/subscriptions/{subscription_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def actualizar_estado_radio(radio, datos_paypal):
    status = datos_paypal.get("status")
    last_payment = datos_paypal.get("billing_info", {}).get("last_payment", {}).get("time")
    next_billing = datos_paypal.get("billing_info", {}).get("next_billing_time")

    hoy = timezone.now().date()

    # Fecha de inicio (último pago)
    if last_payment:
        fecha_inicio = timezone.datetime.fromisoformat(last_payment.replace("Z", "+00:00")).date()
        print(fecha_inicio)
        radio.fecha_inicio = fecha_inicio
    else:
        fecha_inicio = radio.fecha_inicio  # Usa la fecha que ya tenga en la base

    # Días restantes (usamos la fecha de próxima facturación si existe)
    if next_billing:
        fecha_next = timezone.datetime.fromisoformat(next_billing.replace("Z", "+00:00")).date()
        print(fecha_next)
        dias_restantes = (fecha_next - hoy).days-1
        radio.dias_restantes = max(0, dias_restantes)
    else:
        dias_restantes = radio.dias_restantes  # Mantiene el valor actual

    # Estado
    if dias_restantes <= 0:
        radio.estado_suscripcion = "Inactivo"
    else:
        if status == "ACTIVE":
            radio.estado_suscripcion = "Activo"
        elif status == "CANCELLED":
            radio.estado_suscripcion = "Cancelado"
        else:
            # Cualquier otro estado lo tratamos como Cancelado pero con días restantes
            radio.estado_suscripcion = "Cancelado"

    radio.save()
