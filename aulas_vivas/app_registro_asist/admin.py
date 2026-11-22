from django.contrib import admin

# Register your models here.
from .models import RegistroAsistencia, SesionClase

admin.site.register(SesionClase)
admin.site.register(RegistroAsistencia)