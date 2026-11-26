from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Max, Min, Q
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout


from app_nucleo.models import Alumno, Asignatura, Grupo, PeriodoEscolar
from app_registro_asist.models import RegistroAsistencia, SesionClase
from .models import ConfiguracionSemaforo


def _aplicar_filtros_sesiones(sesiones, request):
    grupo_param = request.GET.get("grupo", "").strip()
    asignatura_param = request.GET.get("asignatura", "").strip()
    periodo_param = request.GET.get("periodo", "").strip()

    periodo_obj = None
    if periodo_param.isdecimal():
        periodo_obj = PeriodoEscolar.objects.filter(pk=periodo_param).first()

    if grupo_param:
        grupos = Grupo.objects.filter(codigo=grupo_param)
        if not grupos.exists():
            sesiones = sesiones.none()
        else:
            sesiones = sesiones.filter(grupo=grupo_param)
            if periodo_obj and not grupos.filter(
                periodoEscolar=periodo_obj
            ).exists():
                sesiones = sesiones.none()

    if periodo_param and not periodo_obj:
        sesiones = sesiones.none()
    elif periodo_obj:
        sesiones = sesiones.filter(
            Q(periodoEscolar_id=periodo_obj.pk)
            | Q(
                periodoEscolar__isnull=True,
                fecha__range=(periodo_obj.fechaInicio, periodo_obj.fechaFin),
            )
        )

    if asignatura_param:
        asignatura_obj = None
        if asignatura_param.isdecimal():
            asignatura_obj = Asignatura.objects.filter(pk=asignatura_param).first()
        if asignatura_obj:
            sesiones = sesiones.filter(asignatura=asignatura_obj.nombre)
        else:
            sesiones = sesiones.none()

    return sesiones, {
        "grupo": grupo_param,
        "grupo_nombre": grupo_param,
        "asignatura": asignatura_param,
        "periodo": periodo_param,
        "periodo_nombre": str(periodo_obj) if periodo_obj else "",
    }


# CU05 - ESTADISTICAS
def estadisticas(request):
    sesiones_base = SesionClase.objects.filter(
        estado="CERRADA",
        registros__estado__in=["PRESENTE", "AUSENTE"],
    ).distinct()

    sesiones, filtros_activos = _aplicar_filtros_sesiones(sesiones_base, request)

    registros = RegistroAsistencia.objects.filter(
        sesion__in=sesiones,
        estado__in=["PRESENTE", "AUSENTE"],
    )

    totales = registros.aggregate(
        asistencias=Count("id", filter=Q(estado="PRESENTE")),
        faltas=Count("id", filter=Q(estado="AUSENTE")),
    )
    rango_fechas = sesiones.aggregate(
        fecha_inicio=Min("fecha"),
        fecha_fin=Max("fecha"),
    )

    alumnos_con_faltas = (
        registros.values("matricula", "nombre_alumno")
        .annotate(faltas=Count("id", filter=Q(estado="AUSENTE")))
        .filter(faltas__gt=0)
        .order_by("-faltas", "nombre_alumno")[:5]
    )

    # sesion__grupo ya es el código del grupo (ej. "5A")
    grupos_con_faltas = (
        registros.values("sesion__grupo", "sesion__periodoEscolar__nombre")
        .annotate(faltas=Count("id", filter=Q(estado="AUSENTE")))
        .filter(faltas__gt=0)
        .order_by("-faltas", "sesion__grupo", "sesion__periodoEscolar__nombre")
    )

    faltas_por_dia = [0] * 7
    for fecha in registros.filter(estado="AUSENTE").values_list(
        "sesion__fecha", flat=True
    ):
        if fecha is not None:
            faltas_por_dia[fecha.weekday()] += 1

    chart_data = {
        "attendance": [totales["faltas"] or 0, totales["asistencias"] or 0],
        "students": {
            "labels": [alumno["nombre_alumno"] for alumno in alumnos_con_faltas],
            "values": [alumno["faltas"] for alumno in alumnos_con_faltas],
        },
        "groups": {
            "labels": [
                (
                    f'{grupo["sesion__grupo"]} ({grupo["sesion__periodoEscolar__nombre"]})'
                    if grupo["sesion__periodoEscolar__nombre"]
                    else grupo["sesion__grupo"]
                )
                for grupo in grupos_con_faltas
            ],
            "values": [grupo["faltas"] for grupo in grupos_con_faltas],
        },
        "week": {
            "labels": [
                "Lunes", "Martes", "Miércoles", "Jueves", "Viernes",
                "Sábado", "Domingo",
            ],
            "values": faltas_por_dia,
        },
    }

    # Total de alumnos considerando los registrados y, si hay filtro de grupo, también los del catálogo
    matriculas_registradas = set(
        registros.values_list("matricula", flat=True).distinct()
    )
    total_alumnos = len(matriculas_registradas)

    return render(
        request,
        "app_estadisticas/estadisticas.html",
        {
            "clases": sesiones.count(),
            "alumnos": total_alumnos,
            "asistencias": totales["asistencias"] or 0,
            "faltas": totales["faltas"] or 0,
            "fecha_inicio": rango_fechas["fecha_inicio"],
            "fecha_fin": rango_fechas["fecha_fin"],
            "chart_data": chart_data,
            "filtros_activos": filtros_activos,
        },
    )


# CU06 - SEMAFORO DE FALTAS
def semaforo(request):
    configuracion = ConfiguracionSemaforo.obtener_configuracion()

    sesiones_base = SesionClase.objects.filter(
        estado="CERRADA",
        registros__estado__in=["PRESENTE", "AUSENTE"],
    ).distinct()

    sesiones, filtros_activos = _aplicar_filtros_sesiones(sesiones_base, request)

    registros = (
        RegistroAsistencia.objects.filter(
            sesion__in=sesiones,
            estado__in=["PRESENTE", "AUSENTE"],
        )
        .values("matricula", "nombre_alumno")
        .annotate(
            clases=Count("id"),
            faltas=Count("id", filter=Q(estado="AUSENTE")),
        )
        .order_by("nombre_alumno")
    )

    alumnos = []
    for registro in registros:
        clases_count = registro["clases"] or 0
        porcentaje = (
            (Decimal(registro["faltas"]) / Decimal(clases_count)) * Decimal("100")
            if clases_count > 0
            else Decimal("0.00")
        )
        porcentaje = porcentaje.quantize(Decimal("0.01"))

        if porcentaje < configuracion.limite_amarillo:
            estado = "Verde"
            color = "green"
        elif porcentaje < configuracion.limite_rojo:
            estado = "Amarillo"
            color = "yellow"
        else:
            estado = "Rojo"
            color = "red"

        alumnos.append({
            "matricula": registro["matricula"],
            "nombre": registro["nombre_alumno"],
            "clases": clases_count,
            "faltas": registro["faltas"],
            "porcentaje": porcentaje,
            "estado": estado,
            "color": color,
        })

    fechas = sesiones.aggregate(
        fecha_inicio=Min("fecha"),
        fecha_fin=Max("fecha"),
    )

    return render(
        request,
        "app_estadisticas/semaforo.html",
        {
            "configuracion": configuracion,
            "alumnos": alumnos,
            "grupo": filtros_activos["grupo_nombre"] or "Todos",
            "asignatura": filtros_activos["asignatura"] or "Todas",
            "fecha_inicio": fechas["fecha_inicio"],
            "fecha_fin": fechas["fecha_fin"],
        },
    )


# CU19 - CONFIGURACION DEL SEMAFORO
def configuracion_semaforo(request):
    configuracion = ConfiguracionSemaforo.obtener_configuracion()

    if request.method == "POST":
        configuracion.limite_amarillo = request.POST.get("limite_amarillo")
        configuracion.limite_rojo = request.POST.get("limite_rojo")

        try:
            configuracion.save()
            messages.success(
                request,
                "La configuración del semaforo se guardó correctamente.",
            )
            return redirect("configuracion_semaforo")
        except ValidationError as error:
            messages.error(request, error)

    return render(
        request,
        "app_estadisticas/config_semaforo.html",
        {"configuracion": configuracion},
    )


 # ajusta al nombre de tu vista/URL de inicio de sesión


def filtros(request):
    grupos = (
        Grupo.objects.order_by("codigo")
        .values_list("codigo", flat=True)
        .distinct()
    )
    asignaturas = Asignatura.objects.all().order_by("nombre")
    periodos = PeriodoEscolar.objects.all().order_by("-fechaInicio")

    context = {
        "grupos": grupos,
        "asignaturas": asignaturas,
        "periodos": periodos,
        "grupo_seleccionado": request.GET.get("grupo", ""),
        "asignatura_seleccionada": request.GET.get("asignatura", ""),
        "periodo_seleccionado": request.GET.get("periodo", ""),
    }
    return render(request, "app_estadisticas/filtros.html", context)

@login_required
def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("login")