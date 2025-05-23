import requests
from requests.auth import HTTPBasicAuth
import json
from django.conf import settings

# ========= CONFIGURA AQUÍ =========

PRODUCT_NAME = "Generador de Audio Testigos"
PRODUCT_DESCRIPTION = "Servicio dirigido a radios que graba las transmisiones diarias y procesa el contenido para extraer automáticamente audios testigos de spots gubernamentales. Facilita el cumplimiento de obligaciones y el monitoreo eficiente de campañas transmitidas."
PLAN_NAME = "Plan Estándar – Audio Testigos Diario"
PLAN_DESCRIPTION = "Generación automática de todos los audio testigos diarios de las transmisiones."
CURRENCY = "MXN"
PRICE = "899"

RETURN_URL = "https://bbdf-38-194-232-204.ngrok-free.app/paypal/return/"
CANCEL_URL = "https://bbdf-38-194-232-204.ngrok-free.app/paypal/cancel/"


PAYPAL_CLIENT_ID = "AXlmvwhRDmCIApsu-rZdKuf9XQ7syljnOhe_M3ShS-GaSi_KGmkyn_dY8Ch0FfP5rilQ5CA4JonGK6ZY"
PAYPAL_SECRET = "EHkleW9rVYSnaUbLExa92fuZZ3iBKH7Lxz_3wkIxCM_UbRvVD_7Tfso-5BdzjKwQcZ3RZdQh47_kej6h"
PAYPAL_API_BASE = "https://api-m.paypal.com"

# ==================================

def get_access_token():
    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=HTTPBasicAuth(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        data={'grant_type': 'client_credentials'}
    )
    response.raise_for_status()
    return response.json()['access_token']


def crear_producto(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    data = {
        "name": PRODUCT_NAME,
        "description": PRODUCT_DESCRIPTION,
        "type": "SERVICE",
        "category": "SOFTWARE"
    }

    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/catalogs/products",
        headers=headers,
        json=data
    )

    if response.status_code == 409:
        raise Exception("Ya existe un producto con ese nombre.")

    response.raise_for_status()
    product_id = response.json()['id']
    print(f" Producto creado con ID: {product_id}")
    return product_id


def crear_plan(access_token, product_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    data = {
        "product_id": product_id,
        "name": PLAN_NAME,
        "description": PLAN_DESCRIPTION,
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": PRICE,
                        "currency_code": CURRENCY
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }

    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/billing/plans",
        headers=headers,
        json=data
    )

    response.raise_for_status()
    plan_id = response.json()['id']
    print(f" Plan creado con ID: {plan_id}")
    return plan_id


def main():
    print("Obteniendo Access Token...")
    access_token = get_access_token()

    print(access_token)

    print(" Creando producto...")
    product_id = crear_producto(access_token)

    print(" Creando plan mensual...")
    plan_id = crear_plan(access_token, product_id)

    print(" Todo listo.")
    print(f"Producto ID: {product_id}")
    print(f"Plan ID: {plan_id}")


if __name__ == "__main__":
    main()
