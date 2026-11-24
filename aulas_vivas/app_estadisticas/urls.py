from django.urls import path
from.import views

urlpatterns = [
    # CU05-ESTADISTICAS
    path('estadisticas/', views.estadisticas,name='estadisticas'),

    # CU06- SEMAFORO DE FALATAS
    path('semaforo/', views.semaforo,name='semaforo'),

    # CU19-CONFIGURACION DEL SEMAFORO
    path(
        'configuracion-semaforo/',
        views.configuracion_semaforo,
        name='configuracion_semaforo'
    ),
]
