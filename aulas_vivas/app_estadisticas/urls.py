from django.urls import path
from.import views

urlpatterns = [
    path('', views.estadisticas,name='estadisticas'),
    path('semaforo/', views.semaforo,name='semaforo'),
    path('configuracion-semaforo/',views.configuracion_semaforo,name='configuracion_semaforo'),
    path('cerrar_sesion/', views.cerrar_sesion, name="cerrar_sesion")
    ]
