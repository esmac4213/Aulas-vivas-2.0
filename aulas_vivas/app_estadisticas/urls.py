from django.urls import path
from.import views

urlpatterns = [
    path('', views.estadisticas,name='estadisticas'),
    path('semaforo/', views.semaforo,name='semaforo'),
    path('configuracion-semaforo/',views.configuracion_semaforo,name='configuracion_semaforo'),
    ]
