from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from rest_framework import status
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
import requests
from django.conf import settings
import json
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .services import PayPalClient
from .models import Radio  # Suponiendo un modelo Radio vinculado al usuario
import json
from .forms import UserAndRadioCreationForm
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import redirect
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes
)
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from google.cloud import storage
from google.cloud import pubsub_v1
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Radio
from .serializers import UserSerializer, InfoRadioSerializer
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .signals import listar_archivos, generate_upload_signed_url, generate_download_signed_url
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Radio
import requests
from django.conf import settings

from .utils import consultar_estado_paypal, actualizar_estado_radio


def signup(request):
    if request.method == 'GET':
        form = UserAndRadioCreationForm()
        return render(request, 'signup.html', {"form": form})
    else:
        print(request.POST)
        form = UserAndRadioCreationForm(request.POST)
        print(form)

        if not form.is_valid():
            messages.error(request, "Revisa los datos del formulario.")
            return render(request, "signup.html", {"form": form})

        # El UserCreationForm ya valida si password1 y password2 coinciden.
        # También valida que el username no exista.
        try:
            with transaction.atomic():
                # Crea el usuario
                user = form.save()  # Esto llama a UserCreationForm.save()

                # Crea el Radio asociado a ese usuario
                radio = Radio.objects.create(
                    user=user,
                    nombre_radio=form.cleaned_data['nombre_radio'],
                    siglas=form.cleaned_data['siglas'].upper(),
                    correo_electronico=form.cleaned_data['correo_electronico'],
                    estado=form.cleaned_data['estado'],
                    estado_suscripcion='Inactivo',  # o el que corresponda
                    software=0,
                    fecha_inicio=timezone.now(),
                    dias_restantes=0
                )

                # Genera el token correspondiente
                token = Token.objects.create(user=user)

            # Hace login inmediato
            login(request, user)

            # Redirecciona a donde corresponda
            return redirect('userinfo')


        except IntegrityError as exc:

            # puede venir del username duplicado o siglas duplicadas

            if "unique constraint" in str(exc).lower():

                messages.error(request, "Usuario o siglas ya existentes.")

            else:

                messages.error(request, "Error interno, intenta de nuevo.")

            return render(request, "signup.html", {"form": form})


def home(request):
    return render(request, 'home.html')


def UserGuide(request):
    return render(request, 'UserGuide.html')


def Downloads(request):
    """Vista que muestra el enlace de descarga."""

    client = storage.Client()
    bucket = settings.GCP_BUCKET_NAME
    print(bucket)

    blob_name   = "ArchivosPaginaWeb2025GeneradorAudTestigos/LinkDescarga/Generador_De_Audio_Testigos_Installer.exe"    # ruta dentro del bucket

    signed_url = generate_download_signed_url(bucket, blob_name)

    context = {
        "download_url": signed_url,
        "archivo": blob_name.split("/")[-1],
        "expira": 15,   # minutos
    }

    return render(request, 'Downloads.html',context)


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {"form": AuthenticationForm})
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html',
                          {"form": AuthenticationForm, "error": "Nombre de usuario y/o contraseña es incorrecta"})
        login(request, user)

        return redirect('userinfo')


@login_required
def userinfo(request):
    usuario = request.user
    # Si usas ForeignKey:
    radio = Radio.objects.filter(user=usuario).first()
    # Si ya cambiaste a OneToOneField podrías usar:
    # radio = getattr(usuario, "radio", None)

    if radio and radio.paypal_subscription_id:
        # Obtenemos el estado real desde PayPal
        paypal_client = PayPalClient()
        access_token = paypal_client.get_access_token()

        datos_paypal = consultar_estado_paypal(radio.paypal_subscription_id, access_token)
        actualizar_estado_radio(radio, datos_paypal)
        print('actualizando')

    return render(request, 'userinfo.html', {
        'usuario': usuario,
        'radio': radio,
    })





@login_required
def signout(request):
    logout(request)
    return redirect('home')


@api_view(['POST'])
def ingresar_api(request):
    user = get_object_or_404(User, username=request.data['username'])
    print(user)

    if not user.check_password(request.data['password']):
        return Response({
            'error': 'Contraseña incorrecta',
        }, status=status.HTTP_400_BAD_REQUEST)

    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)

    return Response({
        'token': token.key,
        'User': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def info_suscripcion_api(request):
    radio = Radio.objects.get(user=request.user)

    if radio.paypal_subscription_id:
        paypal_client = PayPalClient()
        access_token = paypal_client.get_access_token()

        datos_paypal = consultar_estado_paypal(radio.paypal_subscription_id, access_token)

        actualizar_estado_radio(radio, datos_paypal)

    infoRadio = InfoRadioSerializer(radio)

    respuesta = infoRadio.data

    return Response(respuesta, status=status.HTTP_200_OK)


# ---------- A. Endpoint que genera la URL de pago ----------
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def crear_carpeta_gcs(request):
    print('crear carpeta')
    """
    Crea una carpeta simulada en el bucket bajo {user_id}/grabaciones_dia/{nombre}
    Espera en el body: {"nombre": "nueva_carpeta"}
    """
    nombre = request.data.get('nombre')
    Categoria_Carpeta = request.data.get('Categoria_Carpeta')
    if not nombre:
        return Response({'error': 'Falta el parámetro "nombre".'}, status=400)

    user_id = request.user.username
    ruta = f"{user_id}/{Categoria_Carpeta}/{nombre}"

    client = storage.Client()
    bucket = client.bucket(settings.GCP_BUCKET_NAME)

    # Verificar si ya hay blobs con ese prefijo
    blobs = list(bucket.list_blobs(prefix=f'{ruta}/'))
    if blobs:
        return Response({'status': 'ya existe', 'ruta': ruta})

    # Crear carpeta simulada con marcador vacío
    blob = bucket.blob(f'{ruta}/.placeholder')
    blob.upload_from_string('')

    return Response({'status': 'creado', 'ruta': ruta})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def borrar_archivo(request):
    """
    Borra un archivo específico en el bucket.
    Espera {"path": "usuario1/grabaciones_dia/26042025/audio1.mp3"}
    """
    user = request.user.username
    path = request.data.get('archivo')

    print(path)


    if not path:
        return Response({'error': 'Falta el parámetro "nombre".'}, status=400)

    client = storage.Client()
    bucket = client.bucket(settings.GCP_BUCKET_NAME)

    blob = bucket.blob(path)

    if not blob.exists():
        return Response({'status': 'no existe', 'archivo': path})

    blob.delete()

    return Response({'status': 'borrado', 'archivo': path})




@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def get_signed_url(request):
    print('holi')

    Categoria_Carpeta = request.data.get('Categoria_Carpeta')
    subCarpeta = request.data.get('SubCarpeta')
    file_name = request.data.get('file_name')
    print(file_name)

    if not subCarpeta:
        return Response({'error': 'Falta el parámetro "subCarpeta".'}, status=400)
    if not file_name:
        return Response({'error': 'Falta el parámetro "file_name".'}, status=400)

    user_id = request.user.username
    bucket_name = settings.GCP_BUCKET_NAME  # Nombre de tu bucket GCS
    ruta = f"{user_id}/{Categoria_Carpeta}/{subCarpeta}/{file_name}"

    print(ruta)

    blob_name = ruta
    print(blob_name)
    content_type = request.data.get('content_type')  # p.ej. "audio/mpeg"
    signed_url = generate_upload_signed_url(bucket_name, blob_name, content_type)
    return Response({'url': signed_url})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def get_signed_download_url(request):
    file_name = request.data.get('file_name')

    bucket_name = settings.GCP_BUCKET_NAME

    blob_name = file_name

    signed_url = generate_download_signed_url(bucket_name, blob_name)  # 👈 función de descarga
    return Response({'url': signed_url})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def listar_archivos_api(request):
    print('entramos')
    user = request.user.username
    ruta = request.data.get('ruta')

    if not ruta:
        return Response({'error': 'Falta el parámetro "ruta".'}, status=400)

    archivos = listar_archivos(settings.GCP_BUCKET_NAME, ruta, user)
    return Response({'archivos': archivos})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def iniciar_generador_api(request):
    usuario = request.user

    user=usuario.username
    fecha = request.data.get('fecha')

    if not fecha:
        return Response({'error': 'Falta el parámetro "fecha".'}, status=400)

    # Obtener información de la radio asociada al usuario
    try:
        radio = Radio.objects.filter(user=usuario).first()
        siglas = radio.siglas
        software = radio.software

    except Radios.DoesNotExist:
        return Response({'error': 'No se encontró información de la radio para este usuario.'}, status=404)


    bucket_name = settings.GCP_BUCKET_NAME

    # Simulación del generador
    print("🟢 Iniciando generador")
    print(f"Usuario: {user}")
    print(f"Fecha: {fecha}")
    print(f"Siglas: {siglas}")
    print(f"Software: {software}")
    print(f"bucket: {bucket_name}")

    return Response({'mensaje': 'Generador iniciado correctamente'})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def upload_complete(request):
    user_id = request.data.get('user_id')
    folder = request.data.get('folder')
    if not user_id or not folder:
        return Response({'error': 'Faltan parámetros.'}, status=status.HTTP_400_BAD_REQUEST)

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        settings.GCP_PROJECT_ID,
        settings.PUBSUB_TOPIC
    )
    message = json.dumps({'user_id': user_id, 'folder': folder})
    publisher.publish(topic_path, message.encode('utf-8'))

    return Response({'status': 'ok'})


def create_subscription(request):
    """Vista para iniciar el proceso de suscripción."""
    if request.method != "POST":
        return HttpResponse(status=405)

    plan_id = settings.PAYPAL_PLAN_ID
    return_url = request.build_absolute_uri(reverse('paypal_return'))
    cancel_url = request.build_absolute_uri(reverse('paypal_cancel'))

    usuario = request.user
    radio = Radio.objects.filter(user=usuario).first()

    if not radio.correo_electronico:
        return HttpResponse(
            "Tu cuenta de usuario no tiene un correo electrónico definido. No se puede crear la suscripción.",
            status=400)

    subscriber = {
        "name": {"given_name": usuario.username },
        "email_address": radio.correo_electronico
    }

    # 🔥 GENERAR EL CUSTOM_ID
    custom_id = f"radio-{radio.siglas}-{radio.nombre_radio}"  # Puedes usar radio.siglas o algo único

    paypal_client = PayPalClient()
    try:
        access_token = paypal_client.get_access_token()

        subscription_id, approve_url = paypal_client.crear_suscripcion_paypal(
            access_token=access_token,
            plan_id=plan_id,
            return_url=return_url,
            cancel_url=cancel_url,
            subscriber=subscriber,
            custom_id=custom_id  # 👈 Le pasamos el custom_id
        )

    except Exception as e:
        return HttpResponse(f"Error al crear suscripción: {e}", status=500)

    # Guardar el ID y el custom_id en el modelo Radio
    radio.paypal_subscription_id = subscription_id
    radio.paypal_custom_id = custom_id
    radio.estado_suscripcion = "Inactivo"  # 👈 CORRECTO (no booleano)
    radio.dias_restantes = 0
    radio.save()

    if approve_url:
        return redirect(approve_url)
    else:
        return HttpResponse("No se encontró la URL de aprobación.", status=400)

def paypal_return(request):
    usuario = request.user

    # Actualizamos el estado de la suscripción a Activo
    radio = Radio.objects.filter(user=usuario).first()
    if radio:
        radio.estado_suscripcion = "Activo"
        radio.dias_restantes = 30  # Puedes poner el número que quieras
        radio.save()

    # Redirigir a userinfo
    return redirect(reverse('userinfo'))


def paypal_cancel(request):
    usuario = request.user

    # Actualizamos el estado de la suscripción a Inactivo
    radio = Radio.objects.filter(user=usuario).first()
    if radio:
        radio.estado_suscripcion = "Inactivo"
        radio.dias_restantes = 0
        radio.save()

    # Redirigir a userinfo
    return redirect(reverse('userinfo'))


@csrf_exempt
def paypal_webhook(request):
    data = json.loads(request.body.decode('utf-8'))
    event_type = data.get("event_type")
    resource = data.get("resource", {})
    subscription_id = resource.get("id")

    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        try:
            radio = Radio.objects.get(paypal_subscription_id=subscription_id)
        except Radio.DoesNotExist:
            return HttpResponse(status=404)
        radio.estado_suscripcion = "Activo"
        radio.fecha_inicio = timezone.now().date()  # 👈 Actualizamos la fecha de inicio
        radio.dias_restantes = 30  # Al inicio siempre le asignas 30 días
        radio.save()

    return HttpResponse(status=200)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def iniciar_proceso(request):
    """
    Inicia un proceso en Google Cloud Run.
    Espera {"fecha": "DDMMAAAA", "siglas": "ABC", "bucket": "nombre-del-bucket"}
    """
    user = request.user.username
    fecha = request.data.get('fecha')
    radio = Radio.objects.filter(user=usuario).first()
    siglas = radio.siglas
    bucket='audio_estigos_project'

    if not all([fecha, siglas, bucket]):
        return Response({'error': 'Faltan parámetros requeridos.'}, status=400)

    # Construir la URL del servicio de Cloud Run
    cloud_run_url = f"https://{settings.CLOUD_RUN_REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{settings.GCP_PROJECT_ID}/services/{settings.CLOUD_RUN_SERVICE_NAME}:run"

    # Payload para la solicitud
    payload = {
        "user": user,
        "bucket": bucket,
        "siglas": siglas,
        "fecha": fecha
    }

    # Encabezados de autenticación
    headers = {
        "Authorization": f"Bearer {settings.GCP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Realizar la solicitud POST al servicio de Cloud Run
    response = requests.post(cloud_run_url, json=payload, headers=headers)

    if response.status_code == 200:
        return Response({'status': 'Proceso iniciado correctamente.'})
    else:
        return Response({'error': 'Error al iniciar el proceso en Cloud Run.', 'details': response.text}, status=500)