import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth


class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        # Seleccionar la base URL según entorno
        if settings.PAYPAL_ENV == 'sandbox':
            print('sandbox')
            self.base_url = 'https://api-m.sandbox.paypal.com'
        else:
            self.base_url = 'https://api-m.paypal.com'

    def get_access_token(self):
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=HTTPBasicAuth(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'}
        )
        response.raise_for_status()
        return response.json()['access_token']

    def crear_suscripcion_paypal(sefl, access_token, plan_id, return_url, cancel_url, subscriber,custom_id):
        """
        Crea una suscripción de PayPal y devuelve el ID de suscripción y el URL de aprobación.

        Parámetros:
            - access_token: str. El token OAuth de PayPal.
            - plan_id: str. ID del plan.
            - return_url: str. URL donde redirige PayPal tras aprobación.
            - cancel_url: str. URL donde redirige si el usuario cancela.
            - subscriber: dict. Diccionario con los datos del suscriptor (nombre y correo).

        Retorna:
            - subscription_id: str
            - approve_url: str
        """

        #https: // api - m.sandbox.paypal.com
        url = "https://api-m.paypal.com/v1/billing/subscriptions"  # Usa sandbox si estás en pruebas

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        payload = {
            "plan_id": plan_id,
            "application_context": {
                "brand_name": "Generador Audio Testigos",
                "locale": "es-MX",
                "user_action": "SUBSCRIBE_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "subscriber": subscriber,
            "custom_id": custom_id  # 👈 Aquí agregamos tu custom_id
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            data = response.json()
            subscription_id = data.get("id")
            approve_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approve_url = link.get("href")
                    break
            return subscription_id, approve_url
        else:
            raise Exception(f"Error al crear suscripción: {response.status_code} - {response.text}")
