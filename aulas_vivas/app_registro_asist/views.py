from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from app_nucleo.models import Alumno, Asignatura, Grupo, PeriodoEscolar
from .models import RegistroAsistencia, SesionClase
from app_estadisticas.views import estadisticas


def seleccionar_clase(request):
    fecha_hoy = timezone.localdate()
    periodo_actual = (
        PeriodoEscolar.objects.filter(
            fechaInicio__lte=fecha_hoy,
            fechaFin__gte=fecha_hoy,
        )
        .order_by("-fechaInicio", "-pk")
        .first()
    )
    grupos = (
        Grupo.objects.filter(periodoEscolar=periodo_actual)
        .order_by("codigo")
        .values_list("codigo", flat=True)
        .distinct()
        if periodo_actual
        else []
    )
    asignaturas = Asignatura.objects.order_by("nombre")
    context = {
        "grupos": grupos,
        "asignaturas": asignaturas,
        "periodo_actual": periodo_actual,
        "fecha_hoy": fecha_hoy,
    }

    if request.method == "POST":
        grupo_codigo = request.POST.get("grupo", "").strip()
        asignatura_nombre = request.POST.get("asignatura", "").strip()
        fecha = request.POST.get("fecha", "").strip()
        horario = request.POST.get("horario", "").strip()

        if not periodo_actual:
            messages.error(
                request,
                "No hay un periodo escolar configurado para la fecha actual.",
            )
            return render(
                request,
                "app_registro_asist/seleccionar_clase.html",
                context,
            )

        if not (grupo_codigo and asignatura_nombre and fecha and horario):
            messages.error(
                request,
                "Completa grupo, asignatura, fecha y horario.",
            )
            return render(
                request,
                "app_registro_asist/seleccionar_clase.html",
                context,
            )

        grupo_obj = Grupo.objects.filter(
            codigo=grupo_codigo,
            periodoEscolar=periodo_actual,
        ).first()
        if not grupo_obj:
            messages.error(
                request,
                "El grupo seleccionado no pertenece al periodo actual.",
            )
            return render(
                request,
                "app_registro_asist/seleccionar_clase.html",
                context,
            )

        asignatura_obj = get_object_or_404(Asignatura, nombre=asignatura_nombre)
        sesion = SesionClase.objects.create(
            grupo=grupo_obj.codigo,
            periodoEscolar=periodo_actual,
            asignatura=asignatura_obj.nombre,
            fecha=fecha,
            horario=horario,
            estado="ABIERTA",
        )

        alumnos_del_grupo = Alumno.objects.filter(grupo=grupo_obj).order_by("matricula")
        for alumno in alumnos_del_grupo:
            RegistroAsistencia.objects.create(
                sesion=sesion,
                matricula=alumno.matricula,
                nombre_alumno=alumno.nombre_completo,
                estado="PENDIENTE",
            )

        return redirect("clase_abierta", sesion_id=sesion.id)

    return render(
        request,
        "app_registro_asist/seleccionar_clase.html",
        context,
    )


# CU02 - Layout 04: Lista de asistencia, QR y cierre de clase
def clase_abierta(request, sesion_id):
    sesion = get_object_or_404(SesionClase, id=sesion_id)

    if request.method == "POST":
        accion = request.POST.get("accion")

        # Registrar asistencia por matrícula (desde lector QR o entrada manual)
        if accion == "registrar_qr" and sesion.estado == "ABIERTA":
            matricula = request.POST.get("matricula", "").strip()
            print(matricula)
            registro = RegistroAsistencia.objects.filter(
                sesion=sesion, matricula=matricula
            ).first()
            if registro:
                registro.estado = "PRESENTE"
                registro.save()
                request.session[f"ultimo_registro_{sesion.id}"] = registro.nombre_alumno
                messages.success(request, f"Asistencia registrada: {registro.nombre_alumno}")
            else:
                messages.warning(request, "No se encontró esa matrícula en la lista.")
            return redirect("clase_abierta", sesion_id=sesion.id)

        # Cerrar clase: pendientes pasan a AUSENTE
        if accion == "cerrar_clase" and sesion.estado == "ABIERTA":
            sesion.registros.filter(estado="PENDIENTE").update(estado="AUSENTE")
            sesion.estado = "CERRADA"
            sesion.save()
            messages.success(
                request,
                "Clase cerrada. Los alumnos pendientes quedaron marcados como ausentes.",
            )
            return redirect("clase_abierta", sesion_id=sesion.id)

    registros = sesion.registros.all().order_by("matricula")
    total_presentes = registros.filter(estado="PRESENTE").count()
    total_pendientes = registros.filter(estado="PENDIENTE").count()
    ultimo_alumno = request.session.get(f"ultimo_registro_{sesion.id}")

    contexto = {
        "sesion": sesion,
        "registros": registros,
        "total_presentes": total_presentes,
        "total_pendientes": total_pendientes,
        "ultimo_alumno": ultimo_alumno,
    }
    return render(request, "app_registro_asist/clase_abierta.html", contexto)


# CU03 - Layout 05: Registro manual (solo alumnos pendientes)
def registro_manual(request, sesion_id):
    sesion = get_object_or_404(SesionClase, id=sesion_id)

    if request.method == "POST" and sesion.estado == "ABIERTA":
        registro_id = request.POST.get("registro_id")
        registro = get_object_or_404(
            RegistroAsistencia, id=registro_id, sesion=sesion
        )
        registro.estado = "PRESENTE"
        registro.save()
        request.session[f"ultimo_registro_{sesion.id}"] = registro.nombre_alumno
        # Al guardar, el alumno deja de tener estado PENDIENTE y sale de esta vista
        return redirect("registro_manual", sesion_id=sesion.id)

    pendientes = sesion.registros.filter(estado="PENDIENTE").order_by("matricula")
    contexto = {
        "sesion": sesion,
        "pendientes": pendientes,
    }
    return render(request, "app_registro_asist/registro_manual.html", contexto)


# CU04 - Layout 06: Cancelar clase (motivo obligatorio)
def cancelar_clase(request, sesion_id):
    sesion = get_object_or_404(SesionClase, id=sesion_id)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        if not motivo:
            messages.error(request, "El motivo de cancelación es obligatorio.")
            return render(
                request,
                "app_registro_asist/cancelar_clase.html",
                {"sesion": sesion},
            )

        sesion.estado = "CANCELADA"
        sesion.motivo_cancelacion = motivo
        sesion.save()
        messages.success(
            request,
            "La clase quedó cancelada. No se registrarán faltas ni se contará en cálculos.",
        )
        return redirect("clase_abierta", sesion_id=sesion.id)

    return render(
        request,
        "app_registro_asist/cancelar_clase.html",
        {"sesion": sesion},
    )

def estadisticas (request):
    return estadisticas