from django.contrib import admin
from django.urls import path, re_path
from pergoapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

    path('signup/', views.signup, name='singup'),
    path('userinfo/', views.userinfo, name='userinfo'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('UserGuide/', views.UserGuide, name='UserGuide'),
    path('Downloads/', views.Downloads, name='Downloads'),
    re_path('signin/api/', views.ingresar_api, name='ingresar_api'),

    re_path('signin/infosuscripcion/', views.info_suscripcion_api, name='info_suscripcion'),

    re_path('api/iniciar_generador', views.iniciar_generador_api, name='iniciar_generador_api'),

    path('crear-suscripcion/', views.create_subscription, name='create_subscription'),
    path('paypal/return/', views.paypal_return, name='paypal_return'),
    path('paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
    path('paypal/webhook/', views.paypal_webhook, name='paypal_webhook'),

    # Alias sin barra para evitar el 500:
    path('paypal/webhook', views.paypal_webhook),

    path('upload/get_signed_download_url/', views.get_signed_download_url, name='get_signed_download_url'),

    path('upload/upload-complete/', views.upload_complete, name='upload-complete'),
    path('upload/get_signed_url/', views.get_signed_url, name='get_signed_url'),
    path('upload/crear_carpeta_gcs/', views.crear_carpeta_gcs, name='crear_carpeta_gcs'),
    path('upload/listar_archivos_api/', views.listar_archivos_api, name='listar_archivos_api'),
    path('upload/borrar_archivo/', views.borrar_archivo, name='borrar_archivo'),

]
