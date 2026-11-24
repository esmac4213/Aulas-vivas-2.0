from datetime import date
from django.db.models import Count, Q
from app_registro_asist.models import RegistroAsistencia
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from.models import ConfiguracionSemaforo


# CU05-ESTADISTICAS
def estadisticas(request):
    return render(
        request,
        'app_estadisticas/estadisticas.html'
    )



# CU06- SEMAFORO DE FALTAS
def semaforo(request):

    configuracion = ConfiguracionSemaforo.obtener_configuracion()

    # Filtros de la consulta
    grupo = '5A'
    asignatura = 'Programación'
    fecha_inicio = date(2026, 11, 9)
    fecha_fin = date(2026, 11, 13)

    # Obtener asistencias reales de las sesiones cerradas
    registros = (
        RegistroAsistencia.objects.filter(
            sesion__grupo=grupo,
            sesion__asignatura=asignatura,
            sesion__fecha__range=(fecha_inicio, fecha_fin),
            sesion__estado='CERRADA',
            estado__in=['PRESENTE', 'AUSENTE']
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
            'grupo': grupo,
            'asignatura': asignatura,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    )


    # Calcular porcentaje y determinar el color
    for alumno in alumnos:

        if alumno['clases'] > 0:

            porcentaje = (
                Decimal(alumno['faltas']) /
                Decimal(alumno['clases'])
            ) * Decimal('100')

        else:
            porcentaje = Decimal('0')

        alumno['porcentaje'] = porcentaje.quantize(
            Decimal('0.01')
        )

        if alumno['porcentaje'] < configuracion.limite_amarillo:
            alumno['estado'] = 'Verde'
            alumno['color'] = 'green'

        elif alumno['porcentaje'] < configuracion.limite_rojo:
            alumno['estado'] = 'Amarillo'
            alumno['color'] = 'yellow'

        else:
            alumno['estado'] = 'Rojo'
            alumno['color'] = 'red'

    return render(
        request,
        'app_estadisticas/semaforo.html',
        {
            'configuracion': configuracion,
            'alumnos': alumnos
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
