from django.db import models

class SesionClase(models.Model):
    ESTADO_CHOICES = [
        ("ABIERTA", "Abierta"),
        ("CERRADA", "Cerrada"),
        ("CANCELADA", "Cancelada"),
    ]

    grupo = models.CharField(max_length=20)
    asignatura = models.CharField(max_length=100)
    fecha = models.DateField()
    horario = models.CharField(max_length=30)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="ABIERTA")
    motivo_cancelacion = models.TextField(blank=True, null=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.grupo} - {self.asignatura} ({self.fecha}) [{self.estado}]"


class RegistroAsistencia(models.Model):
    ESTADO_ASISTENCIA = [
        ("PENDIENTE", "Pendiente"),
        ("PRESENTE", "Presente"),
        ("AUSENTE", "Ausente"),
    ]

    sesion = models.ForeignKey(
        SesionClase,
        on_delete=models.CASCADE,
        related_name="registros",
    )
    matricula = models.CharField(max_length=30)
    nombre_alumno = models.CharField(max_length=120)
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_ASISTENCIA,
        default="PENDIENTE",
    )
    registrado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("sesion", "matricula")

    def __str__(self):
        return f"{self.matricula} - {self.nombre_alumno}: {self.estado}"