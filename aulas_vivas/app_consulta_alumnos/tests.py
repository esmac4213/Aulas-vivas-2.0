from django.test import TestCase
from django.urls import reverse

from app_nucleo.models import Alumno, Grupo


class ConsultaAlumnosTests(TestCase):
    def setUp(self):
        grupo = Grupo.objects.create(codigo="5A")
        self.alumno = Alumno.objects.create(
            matricula="20260001",
            nombre_completo="Ana López",
            grupo=grupo,
        )

    def test_busca_alumno_por_matricula_y_muestra_url_correcta(self):
        pagina = self.client.get(reverse("alumnos"))
        respuesta = self.client.get(
            reverse("obtener_alumno"),
            {"busqueda": self.alumno.matricula.lower()},
        )

        self.assertContains(pagina, 'data-url="/consulta_alumno/obtener-alumno/"')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json(),
            {
                "nombre": "Ana López",
                "matricula": "20260001",
                "grupo": "5A",
            },
        )

    def test_busca_alumno_por_nombre(self):
        respuesta = self.client.get(
            reverse("obtener_alumno"),
            {"busqueda": "Ana"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["matricula"], "20260001")
