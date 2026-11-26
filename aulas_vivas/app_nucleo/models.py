from django.db import models
from datetime import *
class PeriodoEscolar(models.Model):
    def periodoautoini():
            fecha=datetime.now()
            mes = fecha.month
            if mes >= 6 and mes <= 12:
                return date (datetime.now().year,6,1 )
            else:
                return date (datetime.now().year,1,1 )
    def periodoautofin():
                fecha=datetime.now()
                mes = fecha.month
                if mes >= 6 and mes <= 12:
                    return date (datetime.now().year,12,30 )
                else:
                    return date (datetime.now().year,5,30 )
    idperiodoescolar=models.IntegerField( unique=True, primary_key=True)
    fechaInicio=models.DateField( null=False, default=periodoautoini)
    fechaFin=models.DateField( null=False, default=periodoautofin)
    ciclo=models.IntegerField( choices=[(1,"1"),(2,"2")], null=False)
    
class Grupo(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    periodoEscolar= models.ForeignKey(
        PeriodoEscolar,
        on_delete=models.CASCADE,
        related_name="periodo"
    )
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
        null=False
    )

    def __str__(self):
        return f"{self.matricula} - {self.nombre_completo} ({self.grupo.codigo})"