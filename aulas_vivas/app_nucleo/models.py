from django.db import models


class Grupo(models.Model):
    codigo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.codigo


class Asignatura(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Alumno(models.Model):
    matricula = models.CharField(max_length=30, unique=True)
    nombre_completo = models.CharField(max_length=120)
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name="alumnos",
    )

    def __str__(self):
        return f"{self.matricula} - {self.nombre_completo} ({self.grupo.codigo})"