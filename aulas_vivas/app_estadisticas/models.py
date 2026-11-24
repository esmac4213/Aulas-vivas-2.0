
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class ConfiguracionSemaforo(models.Model):

    limite_amarillo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5,
        validators=[
            MinValueValidator(0.01),
            MaxValueValidator(100)
        ],
        verbose_name="Límite amarillo (%)"
    )

    limite_rojo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[
            MinValueValidator(0.01),
            MaxValueValidator(100)
        ],
        verbose_name="Límite rojo (%)"
    )

    actualizado = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Configuración del semáforo"
        verbose_name_plural = "Configuración del semáforo"

    def clean(self):
        super().clean()

        if self.limite_amarillo >= self.limite_rojo:
            raise ValidationError(
                "El límite amarillo debe ser menor que el límite rojo."
            )

    def save(self, *args, **kwargs):
        # Mantener una única configuración general.
        self.pk = 1

        # Validar los valores antes de guardarlos.
        self.full_clean()

        super().save(*args, **kwargs)

    @classmethod
    def obtener_configuracion(cls):
        configuracion, creada = cls.objects.get_or_create(
            pk=1,
            defaults={
                "limite_amarillo": 5,
                "limite_rojo": 10
            }
        )

        return configuracion

    def __str__(self):
        return (
            f"Amarillo: {self.limite_amarillo}% | "
            f"Rojo: {self.limite_rojo}%"
        )
