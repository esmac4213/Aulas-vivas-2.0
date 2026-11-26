from django.test import TestCase
from django.urls import reverse
from datetime import date

from app_registro_asist.models import RegistroAsistencia, SesionClase


class EstadisticasTests(TestCase):
    def setUp(self):
        self.sesion_lunes = self.crear_sesion(
            "5A", "Programación", date(2026, 11, 9), "CERRADA"
        )
        self.sesion_martes = self.crear_sesion(
            "5B", "Bases de Datos", date(2026, 11, 10), "CERRADA"
        )
        self.sesion_abierta = self.crear_sesion(
            "5A", "Programación", date(2026, 11, 11), "ABIERTA"
        )
        self.sesion_cancelada = self.crear_sesion(
            "5A", "Programación", date(2026, 11, 12), "CANCELADA"
        )

        self.crear_registro(self.sesion_lunes, "1", "Ana", "PRESENTE")
        self.crear_registro(self.sesion_lunes, "2", "Beto", "AUSENTE")
        self.crear_registro(self.sesion_martes, "1", "Ana", "AUSENTE")
        self.crear_registro(self.sesion_martes, "3", "Caro", "PRESENTE")
        self.crear_registro(self.sesion_abierta, "1", "Ana", "PRESENTE")
        self.crear_registro(self.sesion_cancelada, "2", "Beto", "AUSENTE")

    @staticmethod
    def crear_sesion(grupo, asignatura, fecha, estado):
        return SesionClase.objects.create(
            grupo=grupo,
            asignatura=asignatura,
            fecha=fecha,
            horario="08:00-09:00",
            estado=estado,
        )

    @staticmethod
    def crear_registro(sesion, matricula, nombre, estado):
        return RegistroAsistencia.objects.create(
            sesion=sesion,
            matricula=matricula,
            nombre_alumno=nombre,
            estado=estado,
        )

    def test_estadisticas_agrega_todos_los_registros_de_sesiones_cerradas(self):
        respuesta = self.client.get(reverse("estadisticas"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["clases"], 2)
        self.assertEqual(respuesta.context["alumnos"], 3)
        self.assertEqual(respuesta.context["asistencias"], 2)
        self.assertEqual(respuesta.context["faltas"], 2)
        self.assertEqual(respuesta.context["chart_data"]["attendance"], [2, 2])
        self.assertEqual(
            respuesta.context["chart_data"]["week"]["values"][:2],
            [1, 1],
        )

    def test_semaforo_incluye_alumnos_de_todos_los_grupos_y_asignaturas(self):
        respuesta = self.client.get(reverse("semaforo"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["grupo"], "Todos")
        self.assertEqual(respuesta.context["asignatura"], "Todas")
        self.assertEqual(len(respuesta.context["alumnos"]), 3)
        ana = next(
            alumno
            for alumno in respuesta.context["alumnos"]
            if alumno["matricula"] == "1"
        )
        self.assertEqual(ana["clases"], 2)
        self.assertEqual(ana["faltas"], 1)
