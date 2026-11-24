from django.test import TestCase
from django.urls import reverse

from .models import RolUsuario, Usuario


class LoginCsrfTests(TestCase):
    def setUp(self):
        self.client = self.client_class(enforce_csrf_checks=True)
        self.usuario = Usuario.objects.create_user(
            nombre_usuario="docente",
            password="Clave-temporal-123!",
            rol=RolUsuario.DOCENTE,
        )

    def test_login_requires_and_accepts_csrf_token(self):
        login_url = reverse("login")
        response = self.client.get(login_url)

        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        csrf_token = self.client.cookies["csrftoken"].value
        credentials = {
            "nombre_usuario": self.usuario.nombre_usuario,
            "password": "Clave-temporal-123!",
        }

        rejected = self.client.post(login_url, credentials)
        self.assertEqual(rejected.status_code, 403)

        accepted = self.client.post(
            login_url,
            {**credentials, "csrfmiddlewaretoken": csrf_token},
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(accepted["Location"], reverse("seleccionar_clase"))
        self.assertIn("_auth_user_id", self.client.session)
