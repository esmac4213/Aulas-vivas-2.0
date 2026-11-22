from django.contrib import admin
from .models import Alumno, Asignatura, Grupo

admin.site.register(Grupo)
admin.site.register(Asignatura)
admin.site.register(Alumno)