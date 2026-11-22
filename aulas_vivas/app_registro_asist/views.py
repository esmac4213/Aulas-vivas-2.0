from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import RegistroAsistencia, SesionClase

# CU02 - Layout 03: Selección de grupo y clase
def seleccionar_clase(request):
    grupos = ["5A", "5B", "5C"]
    asignaturas = ["Programación", "Bases de Datos", "Métodos Numéricos"]

    if request.method == "POST":
        grupo = request.POST.get("grupo", "").strip()
        asignatura = request.POST.get("asignatura", "").strip()
        fecha = request.POST.get("fecha", "").strip()
        horario = request.POST.get("horario", "").strip()

        if not (grupo and asignatura and fecha and horario):
            messages.error(request, "Completa grupo, asignatura, fecha y horario.")
            return render(
                request,
                "app_registro_asist/seleccionar_clase.html",
                {"grupos": grupos, "asignaturas": asignaturas},
            )

        sesion = SesionClase.objects.create(
            grupo=grupo,
            asignatura=asignatura,
            fecha=fecha,
            horario=horario,
            estado="ABIERTA",
        )

        # Lista inicial de ejemplo (en producción se carga desde alumnos del grupo)
        alumnos_iniciales = [
            ("20260001", "Ana López"),
            ("20260002", "Carlos Pérez"),
            ("20260003", "María García"),
            ("20260004", "Luis Hernández"),
        ]
        for matricula, nombre in alumnos_iniciales:
            RegistroAsistencia.objects.create(
                sesion=sesion,
                matricula=matricula,
                nombre_alumno=nombre,
                estado="PENDIENTE",
            )

        return redirect("clase_abierta", sesion_id=sesion.id)

    return render(
        request,
        "app_registro_asist/seleccionar_clase.html",
        {"grupos": grupos, "asignaturas": asignaturas},
    )


# CU02 - Layout 04: Lista de asistencia, QR y cierre de clase
def clase_abierta(request, sesion_id):
    sesion = get_object_or_404(SesionClase, id=sesion_id)

    if request.method == "POST":
        accion = request.POST.get("accion")

        # Registrar asistencia por matrícula (desde lector QR o entrada manual)
        if accion == "registrar_qr" and sesion.estado == "ABIERTA":
            matricula = request.POST.get("matricula", "").strip()
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