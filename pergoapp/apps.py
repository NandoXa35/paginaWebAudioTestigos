from django.apps import AppConfig


class PergoappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pergoapp'

    def ready(self):
        import pergoapp.signals  # importa el módulo para registrar
