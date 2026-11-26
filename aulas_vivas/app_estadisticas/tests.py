from django.test import TestCase
from django.urls import reverse
from datetime import date

from app_nucleo.models import Grupo, PeriodoEscolar
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

    def test_filtra_grupos_con_el_mismo_codigo_segun_periodo(self):
        periodo_anterior = PeriodoEscolar.objects.create(
            idperiodoescolar=1,
            nombre="",
            ciclo=1,
            fechaInicio=date(2025, 1, 1),
            fechaFin=date(2025, 5, 30),
            fechacreacion=date(2024, 12, 1),
        )
        periodo_actual = PeriodoEscolar.objects.create(
            idperiodoescolar=2,
            nombre="",
            ciclo=2,
            fechaInicio=date(2025, 6, 1),
            fechaFin=date(2025, 12, 30),
            fechacreacion=date(2025, 5, 1),
        )
        grupo_anterior = Grupo.objects.create(
            codigo="5A", periodoEscolar=periodo_anterior
        )
        grupo_actual = Grupo.objects.create(
            codigo="5A", periodoEscolar=periodo_actual
        )
        sesion_anterior = self.crear_sesion(
            "5A", "Programación", date(2025, 3, 10), "CERRADA"
        )
        sesion_anterior.periodoEscolar = periodo_anterior
        sesion_anterior.save(update_fields=["periodoEscolar"])
        self.crear_registro(sesion_anterior, "ant-1", "Ana", "AUSENTE")
        sesion_actual = self.crear_sesion(
            "5A", "Programación", date(2025, 8, 10), "CERRADA"
        )
        sesion_actual.periodoEscolar = periodo_actual
        sesion_actual.save(update_fields=["periodoEscolar"])
        self.crear_registro(sesion_actual, "act-1", "Beto", "PRESENTE")

        respuesta = self.client.get(
            reverse("estadisticas"),
            {"grupo": grupo_actual.codigo, "periodo": periodo_actual.pk},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["clases"], 1)
        self.assertEqual(respuesta.context["asistencias"], 1)
        self.assertEqual(respuesta.context["faltas"], 0)
        self.assertEqual(respuesta.context["filtros_activos"]["grupo_nombre"], "5A")

        respuesta_grupo_sin_periodo = self.client.get(
            reverse("estadisticas"), {"grupo": grupo_actual.codigo}
        )
        self.assertEqual(respuesta_grupo_sin_periodo.context["clases"], 3)

        respuesta_periodo_anterior = self.client.get(
            reverse("estadisticas"),
            {"grupo": grupo_actual.codigo, "periodo": periodo_anterior.pk},
        )
        self.assertEqual(respuesta_periodo_anterior.context["clases"], 1)

        respuesta_periodo_incompatible = self.client.get(
            reverse("estadisticas"),
            {"grupo": "5B", "periodo": periodo_actual.pk},
        )
        self.assertEqual(respuesta_periodo_incompatible.context["clases"], 0)

        respuesta_filtros = self.client.get(
            reverse("filtros"),
            {"grupo": grupo_actual.codigo, "periodo": periodo_actual.pk},
        )
        self.assertEqual(
            respuesta_filtros.context["grupo_seleccionado"],
            grupo_actual.codigo,
        )
        self.assertEqual(
            respuesta_filtros.context["periodo_seleccionado"],
            str(periodo_actual.pk),
        )
        self.assertEqual(
            list(respuesta_filtros.context["grupos"]).count("5A"),
            1,
        )
        self.assertNotContains(respuesta_filtros, "Creado:")
        self.assertContains(respuesta_filtros, "Ciclo 2 - 2025 | 01/05/2025")
