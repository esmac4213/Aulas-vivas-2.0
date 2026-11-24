from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class RolUsuario(models.TextChoices):
    INVITADO = "INVITADO", "Invitado"
    DOCENTE = "DOCENTE", "Docente"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class UsuarioManager(BaseUserManager):
    def create_user(self, nombre_usuario, password=None, rol=RolUsuario.INVITADO, **extra_fields):
        if not nombre_usuario:
            raise ValueError("El nombre de usuario es obligatorio.")

        usuario = self.model(
            nombre_usuario=nombre_usuario,
            rol=rol,
            **extra_fields,
        )
        # Cifra (hashea) la contraseña de forma segura; nunca guardes texto plano
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, nombre_usuario, password=None, **extra_fields):
        extra_fields.setdefault("rol", RolUsuario.ADMINISTRADOR)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(
            nombre_usuario=nombre_usuario,
            password=password,
            **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre_usuario = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Nombre de usuario",
    )
    # Recomendado max_length=128 para que quepa el hash completo sin truncarse
    password = models.CharField(
        max_length=128,
        verbose_name="Contraseña",
    )
    rol = models.CharField(
        max_length=15,
        choices=RolUsuario.choices,
        default=RolUsuario.INVITADO,
        verbose_name="Rol",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "nombre_usuario"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre_usuario} ({self.get_rol_display()})"

    @property
    def es_administrador(self):
        return self.rol == RolUsuario.ADMINISTRADOR