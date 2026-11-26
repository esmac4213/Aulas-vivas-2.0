from django.db.models import Count, Max, Min, Q
from app_registro_asist.models import RegistroAsistencia, SesionClase
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from.models import ConfiguracionSemaforo


# CU05-ESTADISTICAS
def estadisticas(request):
    registros = RegistroAsistencia.objects.filter(
        sesion__estado='CERRADA',
        estado__in=['PRESENTE', 'AUSENTE'],
    )
    sesiones = SesionClase.objects.filter(
        estado='CERRADA',
        registros__estado__in=['PRESENTE', 'AUSENTE'],
    ).distinct()
    totales = registros.aggregate(
        asistencias=Count('id', filter=Q(estado='PRESENTE')),
        faltas=Count('id', filter=Q(estado='AUSENTE')),
    )
    rango_fechas = sesiones.aggregate(
        fecha_inicio=Min('fecha'),
        fecha_fin=Max('fecha'),
    )

    alumnos_con_faltas = (
        registros.values('matricula', 'nombre_alumno')
        .annotate(faltas=Count('id', filter=Q(estado='AUSENTE')))
        .filter(faltas__gt=0)
        .order_by('-faltas', 'nombre_alumno')[:5]
    )
    grupos_con_faltas = (
        registros.values('sesion__grupo')
        .annotate(faltas=Count('id', filter=Q(estado='AUSENTE')))
        .filter(faltas__gt=0)
        .order_by('-faltas', 'sesion__grupo')
    )

    faltas_por_dia = [0] * 7
    for fecha in registros.filter(estado='AUSENTE').values_list(
        'sesion__fecha', flat=True
    ):
        faltas_por_dia[fecha.weekday()] += 1

    chart_data = {
        'attendance': [totales['faltas'], totales['asistencias']],
        'students': {
            'labels': [alumno['nombre_alumno'] for alumno in alumnos_con_faltas],
            'values': [alumno['faltas'] for alumno in alumnos_con_faltas],
        },
        'groups': {
            'labels': [grupo['sesion__grupo'] for grupo in grupos_con_faltas],
            'values': [grupo['faltas'] for grupo in grupos_con_faltas],
        },
        'week': {
            'labels': [
                'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes',
                'Sábado', 'Domingo',
            ],
            'values': faltas_por_dia,
        },
    }

    return render(
        request,
        'app_estadisticas/estadisticas.html',
        {
            'clases': sesiones.count(),
            'alumnos': registros.values('matricula').distinct().count(),
            'asistencias': totales['asistencias'],
            'faltas': totales['faltas'],
            'fecha_inicio': rango_fechas['fecha_inicio'],
            'fecha_fin': rango_fechas['fecha_fin'],
            'chart_data': chart_data,
        },
    )


# CU06- SEMAFORO DE FALTAS
def semaforo(request):

    configuracion = ConfiguracionSemaforo.obtener_configuracion()

    sesiones = SesionClase.objects.filter(
        estado='CERRADA',
        registros__estado__in=['PRESENTE', 'AUSENTE'],
    ).distinct()
    registros = (
        RegistroAsistencia.objects.filter(
            sesion__in=sesiones,
            estado__in=['PRESENTE', 'AUSENTE'],
        )
        .values('matricula', 'nombre_alumno')
        .annotate(
            clases=Count('id'),
            faltas=Count(
                'id',
                filter=Q(estado='AUSENTE')
            )
        )
        .order_by('nombre_alumno')
    )

    alumnos = []

    # Calcular porcentaje y determinar el color
    for registro in registros:

        porcentaje = (
            Decimal(registro['faltas']) /
            Decimal(registro['clases'])
        ) * Decimal('100')

        porcentaje = porcentaje.quantize(Decimal('0.01'))

        if porcentaje < configuracion.limite_amarillo:
            estado = 'Verde'
            color = 'green'

        elif porcentaje < configuracion.limite_rojo:
            estado = 'Amarillo'
            color = 'yellow'

        else:
            estado = 'Rojo'
            color = 'red'

        alumnos.append({
            'matricula': registro['matricula'],
            'nombre': registro['nombre_alumno'],
            'clases': registro['clases'],
            'faltas': registro['faltas'],
            'porcentaje': porcentaje,
            'estado': estado,
            'color': color
        })

    return render(
        request,
        'app_estadisticas/semaforo.html',
        {
            'configuracion': configuracion,
            'alumnos': alumnos,
            'grupo': 'Todos',
            'asignatura': 'Todas',
            'fecha_inicio': sesiones.aggregate(fecha_inicio=Min('fecha'))[
                'fecha_inicio'
            ],
            'fecha_fin': sesiones.aggregate(fecha_fin=Max('fecha'))[
                'fecha_fin'
            ],
        }
    )



# CU19- CONFIGURACION DEL SEMAFORO
def configuracion_semaforo(request):

    configuracion = ConfiguracionSemaforo.obtener_configuracion()

    if request.method == 'POST':
        configuracion.limite_amarillo = request.POST.get('limite_amarillo')
        configuracion.limite_rojo = request.POST.get('limite_rojo')

        try:
            configuracion.save()
            messages.success(
                request,
                'La configuración del semaforo se guardó correctamente.'
            )
            return redirect('configuracion_semaforo')

        except ValidationError as error:
            messages.error(request, error)

    return render(
        request,
        'app_estadisticas/config_semaforo.html',
        {'configuracion': configuracion}
    )

def cerrar_sesion(request):
    pass