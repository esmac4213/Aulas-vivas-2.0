from django.core.management.base import BaseCommand
from app_nucleo.models import Alumno, Asignatura, Grupo

class Command(BaseCommand):
    help = "Carga datos hipotéticos iniciales de grupos, asignaturas y alumnos."

    def handle(self, *args, **options):
        codigos_grupos = ["5A", "5B"]
        grupos_creados = {}
        for codigo in codigos_grupos:
            grupo_obj, _ = Grupo.objects.get_or_create(codigo=codigo)
            grupos_creados[codigo] = grupo_obj

        nombres_asignaturas = [
            "Programación",
            "Bases de Datos",
            "Métodos Numéricos",
        ]
        for nombre in nombres_asignaturas:
            Asignatura.objects.get_or_create(nombre=nombre)

        alumnos_5a = [
            ("20260001", "Ana López"),
            ("20260002", "Carlos Pérez"),
            ("20260003", "María García"),
            ("20260004", "Luis Hernández"),
            ("242H17021", "Jose Julian")
        ]
        for matricula, nombre_completo in alumnos_5a:
            Alumno.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "nombre_completo": nombre_completo,
                    "grupo": grupos_creados["5A"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Datos hipotéticos base cargados correctamente.")
        )