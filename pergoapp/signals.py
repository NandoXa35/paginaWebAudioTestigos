import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from google.cloud import storage
from django.conf import settings

BUCKET_NAME = settings.GCP_BUCKET_NAME  #
SUBFOLDERS = ("grabaciones_dia", "audios_generados", "Campañas","Configuracion","Logs","Informes")


def generate_upload_signed_url(bucket_name, blob_name, content_type=None):
    client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type=content_type
    )
    return url


def generate_signed_url_with_headers(bucket_name, blob_name, expiration_minutes=15, http_method="GET", headers=None):
    """
    Genera una URL firmada para acceder a un objeto en Google Cloud Storage con encabezados personalizados.

    :param bucket_name: Nombre del bucket en Google Cloud Storage.
    :param blob_name: Nombre del objeto (archivo) dentro del bucket.
    :param expiration_minutes: Tiempo en minutos que la URL firmada será válida.
    :param http_method: Método HTTP permitido (por ejemplo, 'GET', 'PUT').
    :param headers: Diccionario de encabezados personalizados que deben incluirse en la solicitud.
    :return: URL firmada que puede ser utilizada para acceder al objeto con los encabezados especificados.
    """
    # Crear un cliente de almacenamiento
    client = storage.Client()

    # Obtener el objeto (blob) del bucket
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Establecer los encabezados predeterminados si no se proporcionan
    if headers is None:
        headers = {}

    # Incluir encabezados personalizados en la solicitud
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method=http_method,
        headers=headers
    )

    return signed_url

def generate_download_signed_url(bucket_name, blob_name, expiration_minutes=15):
    storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="GET",
    )
    return url

def listar_archivos(bucket_name, nom_Carpeta, user):
    client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = client.bucket(bucket_name)

    ruta = f"{user}/{nom_Carpeta}"


    blobs = bucket.list_blobs(prefix=ruta)  # Ej: '123/grabaciones_dia/26042025/'


    archivos = []
    for blob in blobs:
        if not blob.name.endswith('/'):
            archivos.append(blob.name)

    return archivos


@receiver(post_save, sender=User)
def bootstrap_carpetas_usuario(sender, instance, created, **kwargs):
    if not created:
        return

    bucket = storage.Client(credentials=settings.GS_CREDENTIALS).bucket(settings.GCP_BUCKET_NAME)
    user_prefix = f"{instance.username}/"  # ← ahora usa username

    for sub in SUBFOLDERS:
        blob_name = f"{user_prefix}{sub}/.placeholder"
        bucket.blob(blob_name).upload_from_string("")  # crea marcador vacío
