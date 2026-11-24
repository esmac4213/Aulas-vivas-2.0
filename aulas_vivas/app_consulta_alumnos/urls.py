from django.urls import path
from . import views

urlpatterns = [
    path('', views.consulta_alumnos, name = 'alumnos'),
    path('obtener-alumno/', views.obtener_alumno, name='obtener_alumno'),
]