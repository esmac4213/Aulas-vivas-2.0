from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from app_nucleo.models import Alumno, Asignatura, Grupo, PeriodoEscolar
from .models import RegistroAsistencia, SesionClase


class SeleccionarClaseTests(TestCase):
    def setUp(self):
        self.fecha_hoy = timezone.localdate()
        self.periodo_actual = PeriodoEscolar.objects.create(
            idperiodoescolar=101,
            nombre="",
            fechacreacion=self.fecha_hoy,
            fechaInicio=self.fecha_hoy,
            fechaFin=self.fecha_hoy,
            ciclo=2,
        )
        self.periodo_siguiente = PeriodoEscolar.objects.create(
            idperiodoescolar=102,
            nombre="",
            fechacreacion=self.fecha_hoy,
            fechaInicio=self.fecha_hoy + timedelta(days=1),
            fechaFin=self.fecha_hoy + timedelta(days=30),
            ciclo=1,
        )
        self.grupo_actual = Grupo.objects.create(
            codigo="5A",
            periodoEscolar=self.periodo_actual,
        )
        self.grupo_siguiente = Grupo.objects.create(
            codigo="5A",
            periodoEscolar=self.periodo_siguiente,
        )
        self.alumno_actual = Alumno.objects.create(
            matricula="actual-1",
            nombre_completo="Alumno del periodo actual",
            grupo=self.grupo_actual,
        )
        Alumno.objects.create(
            matricula="siguiente-1",
            nombre_completo="Alumno del periodo siguiente",
            grupo=self.grupo_siguiente,
        )
        Asignatura.objects.create(nombre="Programación")

    def test_asigna_periodo_actual_y_sus_alumnos_sin_pedirlo_en_formulario(self):
        respuesta_formulario = self.client.get(reverse("seleccionar_clase"))

        self.assertEqual(list(respuesta_formulario.context["grupos"]), ["5A"])
        self.assertNotContains(respuesta_formulario, 'name="periodo"')

        respuesta = self.client.post(
            reverse("seleccionar_clase"),
            {
                "grupo": "5A",
                "asignatura": "Programación",
                "fecha": self.fecha_hoy.isoformat(),
                "horario": "08:00 - 09:00",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        sesion = SesionClase.objects.get()
        self.assertEqual(sesion.periodoEscolar, self.periodo_actual)
        self.assertEqual(
            list(
                RegistroAsistencia.objects.filter(sesion=sesion).values_list(
                    "matricula", flat=True
                )
            ),
            [self.alumno_actual.matricula],
        )
