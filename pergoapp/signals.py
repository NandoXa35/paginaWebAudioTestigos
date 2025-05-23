import datetime

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from google.cloud import storage
from django.conf import settings

BUCKET_NAME = settings.GCP_BUCKET_NAME  # "gcs-bucket-audiotestigos"
SUBFOLDERS = ("grabaciones_dia", "audios_generados", "Campañas","Configuracion","Logs","Informes")


def generate_upload_signed_url(bucket_name, blob_name, content_type=None):
    print(blob_name)
    print(bucket_name)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type=content_type
    )
    return url

def generate_download_signed_url(bucket_name, blob_name, expiration_minutes=15):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="GET",
    )
    return url

def listar_archivos(bucket_name, nom_Carpeta, user):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    ruta = f"{user}/{nom_Carpeta}"

    print(ruta)

    blobs = bucket.list_blobs(prefix=ruta)  # Ej: '123/grabaciones_dia/26042025/'

    print(blobs)

    archivos = []
    for blob in blobs:
        if not blob.name.endswith('/'):
            archivos.append(blob.name)

    return archivos


@receiver(post_save, sender=User)
def bootstrap_carpetas_usuario(sender, instance, created, **kwargs):
    if not created:
        return

    bucket = storage.Client().bucket(settings.GCP_BUCKET_NAME)
    user_prefix = f"{instance.username}/"  # ← ahora usa username

    for sub in SUBFOLDERS:
        blob_name = f"{user_prefix}{sub}/.placeholder"
        bucket.blob(blob_name).upload_from_string("")  # crea marcador vacío
