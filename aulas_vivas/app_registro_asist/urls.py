from django.urls import path

from . import views

urlpatterns = [
    path("", views.seleccionar_clase, name="seleccionar_clase"),
    path("sesion/<int:sesion_id>/", views.clase_abierta, name="clase_abierta"),
    path("sesion/<int:sesion_id>/manual/", views.registro_manual,name="registro_manual",),
    path("sesion/<int:sesion_id>/cancelar/",views.cancelar_clase,name="cancelar_clase",),
]