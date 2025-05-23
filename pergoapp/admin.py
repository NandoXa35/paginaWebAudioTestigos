from django.contrib import admin
from pergoapp import models


class EstadoSuscripcionAdmin(admin.ModelAdmin):
    # Especificamos qué campos mostrar en la lista de objetos del admin
    list_display = (
        'siglas', 'estado_suscripcion', 'fecha_inicio', 'dias_restantes', 'nombre_radio', 'estado','software')


admin.site.register(models.Radio, EstadoSuscripcionAdmin)
