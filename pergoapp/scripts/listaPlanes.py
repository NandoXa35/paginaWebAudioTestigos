import requests
from requests.auth import HTTPBasicAuth


PAYPAL_CLIENT_ID = "AXlmvwhRDmCIApsu-rZdKuf9XQ7syljnOhe_M3ShS-GaSi_KGmkyn_dY8Ch0FfP5rilQ5CA4JonGK6ZY"
PAYPAL_CLIENT_SECRET  = "EHkleW9rVYSnaUbLExa92fuZZ3iBKH7Lxz_3wkIxCM_UbRvVD_7Tfso-5BdzjKwQcZ3RZdQh47_kej6h"
# ========= CONFIGURACIÓN =========
client_id = PAYPAL_CLIENT_ID
secret = PAYPAL_CLIENT_SECRET

base_url = "https://api-m.paypal.com"  # Cambia a api-m.paypal.com en producción

# ========= 1️⃣ Obtener Access Token =========
def obtener_access_token():
    url = f"{base_url}/v1/oauth2/token"
    response = requests.post(
        url,
        auth=HTTPBasicAuth(client_id, secret),
        data={"grant_type": "client_credentials"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# ========= 2️⃣ Listar Productos =========
def obtener_productos(token):
    url = f"{base_url}/v1/catalogs/products"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("products", [])

# ========= 3️⃣ Listar Planes =========
def obtener_planes(token):
    url = f"{base_url}/v1/billing/plans"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("plans", [])

# ========= 4️⃣ Mostrar resultados =========
def mostrar_resultados():
    token = obtener_access_token()
    print("🔑 Access Token obtenido correctamente.\n")

    # Productos
    productos = obtener_productos(token)
    print("📦 Productos encontrados:")
    if productos:
        for p in productos:
            print(f"- ID: {p['id']} | Nombre: {p['name']} | Tipo: {p.get('type', 'N/A')}")
    else:
        print("No se encontraron productos.")

    print("\n")

    # Planes
    planes = obtener_planes(token)
    print("📝 Planes encontrados:")
    if planes:
        for plan in planes:
            print(f"- ID: {plan['id']} | Estado: {plan['status']} | Producto ID: {plan.get('product_id', 'N/A')}")
    else:
        print("No se encontraron planes.")

# ========= Ejecutar =========
if __name__ == "__main__":
    mostrar_resultados()
