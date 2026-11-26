from datetime import date
from django.core.management.base import BaseCommand
from app_login.models import RolUsuario, Usuario
from app_nucleo.models import Alumno, Asignatura, Grupo, PeriodoEscolar
from app_registro_asist.models import RegistroAsistencia, SesionClase


class Command(BaseCommand):
    help = (
        "Carga datos hipotéticos de periodos, grupos (incluso con código repetido "
        "en distintos periodos), asignaturas, alumnos e inasistencias."
    )

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

        # 1. Periodos escolares (con idperiodoescolar explícito por ser PK no autoincremental)
        periodos_def = [
            (1, date(2024, 6, 1), date(2024, 12, 30), 1, date(2024, 6, 1)),
            (2, date(2025, 6, 1), date(2025, 12, 30), 2, date(2025, 6, 1)),
            (3, date(2024, 1, 1), date(2024, 5, 30), 2, date(2024, 1, 1)),
            (4, date(2026, 6, 2), date(2026, 12, 29), 2, date(2026, 6, 2)),
            (5, date(2025, 1, 10), date(2025, 5, 30), 1, date(2025, 1, 10)),
        ]
        periodos_por_id = {}
        for pid, f_ini, f_fin, ciclo, fecha_creacion in periodos_def:
            p_obj, _ = PeriodoEscolar.objects.get_or_create(
                idperiodoescolar=pid,
                defaults={
                    "fechaInicio": f_ini,
                    "fechaFin": f_fin,
                    "ciclo": ciclo,
                    "fechacreacion": fecha_creacion,
                },
            )
            cambios_periodo = []
            if p_obj.fechaInicio != f_ini:
                p_obj.fechaInicio = f_ini
                cambios_periodo.append("fechaInicio")
            if p_obj.fechaFin != f_fin:
                p_obj.fechaFin = f_fin
                cambios_periodo.append("fechaFin")
            if p_obj.ciclo != ciclo:
                p_obj.ciclo = ciclo
                cambios_periodo.append("ciclo")
            if p_obj.fechacreacion != fecha_creacion:
                p_obj.fechacreacion = fecha_creacion
                cambios_periodo.append("fechacreacion")
            if cambios_periodo:
                p_obj.save(update_fields=cambios_periodo)
            periodos_por_id[pid] = p_obj

        # 2. Grupos en distintos periodos (incluyendo "5A" repetido en varios periodos)
        grupos_def = [
            ("5A", 1),
            ("5A", 2),
            ("5A", 4),
            ("5B", 2),
            ("5B", 5),
            ("5C", 3),
            ("5C", 1),
            ("5D", 4),
            ("5D", 2),
        ]
        grupos_creados = {}
        for codigo, pid in grupos_def:
            periodo_obj = periodos_por_id[pid]
            grupo_obj, _ = Grupo.objects.get_or_create(
                codigo=codigo,
                periodoEscolar=periodo_obj,
            )
            grupos_creados[(codigo, pid)] = grupo_obj

        # 3. Asignaturas
        nombres_asignaturas = [
            "Programación",
            "Bases de Datos",
            "Métodos Numéricos",
            "Redes de Computadoras",
        ]
        for nombre in nombres_asignaturas:
            Asignatura.objects.get_or_create(nombre=nombre)

        # 4. Alumnos distribuidos en distintos grupos y periodos
        alumnos_def = [
            # 5A - Periodo 1
            ("20260001", "Ana López", ("5A", 1)),
            ("20260002", "Carlos Pérez", ("5A", 1)),
            ("20260003", "María García", ("5A", 1)),
            # 5A - Periodo 2
            ("20260011", "Fernanda Soto", ("5A", 2)),
            ("20260012", "Ricardo León", ("5A", 2)),
            ("20260013", "Daniela Vega", ("5A", 2)),
            ("20260023", "Gabriel Torres", ("5A", 2)),
            # 5A - Periodo 4
            ("20260021", "Emiliano Cruz", ("5A", 4)),
            ("20260022", "Camila Flores", ("5A", 4)),
            # 5B - Periodo 2 y Periodo 5
            ("20260004", "Luis Hernández", ("5B", 2)),
            ("20260005", "Sofía Mendoza", ("5B", 2)),
            ("20260006", "Diego Morales", ("5B", 5)),
            ("20260014", "Valeria Reyes", ("5B", 5)),
            # 5C - Periodo 3 y Periodo 1
            ("20260007", "Elena Ruiz", ("5C", 3)),
            ("20260008", "Mateo Castro", ("5C", 3)),
            ("20260015", "Andrés Navarro", ("5C", 1)),
            # 5D - Periodo 4 y Periodo 2
            ("242H17021", "Jose Julian", ("5D", 4)),
            ("242H17085", "Valeria del Rocio", ("5D", 4)),
            ("242H17029", "Valeria Cordova", ("5D", 2)),
            ("20260016", "Sebastián Silva", ("5D", 2)),
        ]

        for matricula, nombre_completo, clave_grupo in alumnos_def:
            grupo_obj = grupos_creados[clave_grupo]
            alumno_obj, _ = Alumno.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "nombre_completo": nombre_completo,
                    "grupo": grupo_obj,
                },
            )
            if alumno_obj.grupo_id != grupo_obj.pk:
                alumno_obj.grupo = grupo_obj
                alumno_obj.save()

        # 5. Sesiones cerradas e inasistencias en grupos y periodos variados
        # Tupla: (codigo_grupo, id_periodo, asignatura, fecha, horario, estados_por_alumno)
        sesiones_def = [
            # 5A en Periodo 1 (2024)
            ("5A", 1, "Programación", date(2024, 9, 2), "07:00 - 09:00", ["AUSENTE", "PRESENTE", "AUSENTE"]),
            ("5A", 1, "Bases de Datos", date(2024, 9, 4), "09:00 - 11:00", ["PRESENTE", "AUSENTE", "AUSENTE"]),
            # 5A en Periodo 2 (2025) - mismo código "5A", distinto periodo
            ("5A", 2, "Programación", date(2025, 7, 7), "07:00 - 09:00", ["AUSENTE", "PRESENTE", "PRESENTE", "PRESENTE"]),
            ("5A", 2, "Programación", date(2025, 7, 14), "07:00 - 09:00", ["AUSENTE", "AUSENTE", "PRESENTE", "PRESENTE"]),
            ("5A", 2, "Programación", date(2025, 7, 21), "07:00 - 09:00", ["AUSENTE", "AUSENTE", "AUSENTE", "PRESENTE"]),
            ("5A", 2, "Métodos Numéricos", date(2025, 7, 9), "11:00 - 13:00", ["AUSENTE", "PRESENTE", "AUSENTE"]),
            # 5A en Periodo 4 (2026) - mismo código "5A", otro periodo
            ("5A", 4, "Redes de Computadoras", date(2026, 8, 10), "09:00 - 11:00", ["AUSENTE", "AUSENTE"]),
            ("5A", 4, "Programación", date(2026, 8, 12), "07:00 - 09:00", ["PRESENTE", "AUSENTE"]),

            # 5B en Periodo 2 y Periodo 5
            ("5B", 2, "Bases de Datos", date(2025, 8, 12), "09:00 - 11:00", ["PRESENTE", "AUSENTE"]),
            ("5B", 2, "Métodos Numéricos", date(2025, 8, 14), "11:00 - 13:00", ["AUSENTE", "AUSENTE"]),
            ("5B", 5, "Programación", date(2025, 3, 3), "07:00 - 09:00", ["AUSENTE", "PRESENTE"]),
            ("5B", 5, "Redes de Computadoras", date(2025, 3, 5), "09:00 - 11:00", ["PRESENTE", "AUSENTE"]),

            # 5C en Periodo 3 y Periodo 1
            ("5C", 3, "Programación", date(2024, 3, 4), "07:00 - 09:00", ["AUSENTE", "PRESENTE"]),
            ("5C", 3, "Bases de Datos", date(2024, 3, 7), "09:00 - 11:00", ["AUSENTE", "AUSENTE"]),
            ("5C", 1, "Métodos Numéricos", date(2024, 10, 3), "11:00 - 13:00", ["AUSENTE"]),

            # 5D en Periodo 4 y Periodo 2
            ("5D", 4, "Programación", date(2026, 9, 14), "07:00 - 09:00", ["PRESENTE", "AUSENTE"]),
            ("5D", 4, "Redes de Computadoras", date(2026, 9, 16), "09:00 - 11:00", ["AUSENTE", "AUSENTE"]),
            ("5D", 2, "Bases de Datos", date(2025, 10, 8), "11:00 - 13:00", ["AUSENTE", "PRESENTE"]),
        ]

        for codigo_grupo, pid, asignatura, fecha_ses, horario_ses, estados in sesiones_def:
            sesion_obj, _ = SesionClase.objects.get_or_create(
                grupo=codigo_grupo,
                periodoEscolar=periodos_por_id[pid],
                asignatura=asignatura,
                fecha=fecha_ses,
                horario=horario_ses,
                defaults={"estado": "CERRADA"},
            )
            if sesion_obj.estado != "CERRADA":
                sesion_obj.estado = "CERRADA"
                sesion_obj.save()

            alumnos_del_grupo = Alumno.objects.filter(
                grupo=grupos_creados[(codigo_grupo, pid)]
            ).order_by("matricula")

            for idx, alumno_obj in enumerate(alumnos_del_grupo):
                estado_asist = estados[idx % len(estados)]
                RegistroAsistencia.objects.update_or_create(
                    sesion=sesion_obj,
                    matricula=alumno_obj.matricula,
                    defaults={
                        "nombre_alumno": alumno_obj.nombre_completo,
                        "estado": estado_asist,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Datos hipotéticos base, grupos por periodo, alumnos e inasistencias cargados correctamente."
            )
        )