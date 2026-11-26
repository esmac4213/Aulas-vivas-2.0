from django.core.management.base import BaseCommand
from app_login.models import Usuario, RolUsuario
from app_nucleo.models import Alumno, Asignatura, Grupo, PeriodoEscolar
from datetime import *
class Command(BaseCommand):
    help = "Carga datos hipotéticos iniciales de grupos, asignaturas y alumnos."

    def handle(self, *args, **options):
        usuario, creado = Usuario.objects.get_or_create(
        nombre_usuario="prueba",
        defaults={
            "rol": RolUsuario.INVITADO,
            "is_active": True,
            "is_staff": False,
        },
    )
        if creado:
            usuario.set_password("Julian453")
            usuario.save()
        codigos_grupos = ["5A", "5B", "5C","5D"]
        grupos_creados = {}
        periodosIni=[date(2024,6,1),date(2025,6,1),date(2024,1,1), date(2026,6,2)]
        periodosFin=[date(2024,12,30),date(2025,12,30),date(2024,5,30), date(2026,12,29)]
        ciclos=["1","2","2","2"]
        for i,a,c in zip(periodosIni, periodosFin, ciclos):
            periodo_obj, _ = PeriodoEscolar.objects.get_or_create(fechaInicio=i, fechaFin=a, ciclo=c)
        pks = list(PeriodoEscolar.objects.values_list("pk", flat=True))
        for codigo, pk in zip(codigos_grupos, pks):
            grupo_obj, _ = Grupo.objects.get_or_create(codigo=codigo, periodoEscolar_id=pk)
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
            ("242H17021", "Jose Julian"),
            ("242H17085", "Valeria del Rocio"),
            ("242H17029", "Valeria Cordova")
        ]
        for matricula, nombre_completo in alumnos_5a:
            Alumno.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "nombre_completo": nombre_completo,
                    "grupo": grupos_creados["5D"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Datos hipotéticos base cargados correctamente.")
        )