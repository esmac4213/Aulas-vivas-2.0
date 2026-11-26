from django.shortcuts import render
from django.http.response import JsonResponse
from django.db.models import Q
from app_nucleo.models import Alumno


def obtener_alumno(request):

    busqueda = request.GET.get('busqueda', '').strip()

    if not busqueda:
        return JsonResponse(
            {'error': 'Ingresa una matrícula o nombre'},
            status=400
        )

    alumno = Alumno.objects.filter(
        Q(matricula__iexact=busqueda) |
        Q(nombre_completo__icontains=busqueda)
    ).select_related('grupo').first()

    if not alumno:
        return JsonResponse(
            {'error': 'No se encontró el alumno'},
            status=404
        )

    datos = {
        'nombre': alumno.nombre_completo,
        'matricula': alumno.matricula,
        'grupo': alumno.grupo.codigo
    }

    return JsonResponse(datos)

def consulta_alumnos(request):
    return render(request, "alumnos.html")