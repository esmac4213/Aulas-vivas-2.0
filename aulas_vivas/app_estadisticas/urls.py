from django.urls import path
from.import views
from app_login.views import cerrar_sesion

urlpatterns = [
    path('', views.estadisticas,name='estadisticas'),
    path('semaforo/', views.semaforo,name='semaforo'),
    path('configuracion-semaforo/',views.configuracion_semaforo,name='configuracion_semaforo'),
    path('filtros/', views.filtros, name="filtros"),
    path('cerrar_sesion/', views.cerrar_sesion, name="CerrarSesion")
    ]
