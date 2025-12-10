from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from inventario.models import Producto

User = get_user_model()

#   TRABAJADORES Y TURNOS
class Trabajador(models.Model):
    TURNO_CHOICES = [
        ('DIA', 'Día (11:00 - 19:00)'),
        ('NOCHE', 'Noche (19:00 - 01:00)'),
    ]

    nombre = models.CharField(max_length=100)
    turno_base = models.CharField(
        max_length=10,
        choices=TURNO_CHOICES,
        help_text="Turno que normalmente trabaja (día o noche)."
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Turno(models.Model):
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.CASCADE,
        related_name='turnos'
    )
    fecha = models.DateField(auto_now_add=True)
    hora_inicio = models.DateTimeField(null=True, blank=True)
    hora_fin = models.DateTimeField(null=True, blank=True)

    # TIPO DE TURNO
    turno_tipo = models.CharField(max_length=10)

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.trabajador.nombre} - {self.turno_tipo} - {self.fecha}"


# MODELO VENTA

class Venta(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("CONFIRMADA", "Confirmada"),
        ("ANULADA", "Anulada"),
    ]

    fecha = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas",
    )

    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")

    anulada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas_anuladas",
    )
    motivo_anulacion = models.TextField(blank=True, null=True)
    anulada_en = models.DateTimeField(null=True, blank=True)

    # TRABAJADOR Y TURNO
    trabajador = models.ForeignKey(
        Trabajador,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas_trabajador",
    )

    turno = models.ForeignKey(
        Turno,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas_turno",
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha:%Y-%m-%d %H:%M}"

    @transaction.atomic
    def anular(self, usuario=None, motivo=""):
        """
        Anula una venta y devuelve el stock a los productos.
        """
        if self.estado == "ANULADA":
            return

        for item in self.items.all():
            producto = item.producto
            producto.stock += item.cantidad
            producto.save()

        self.estado = "ANULADA"
        self.motivo_anulacion = motivo
        self.anulada_en = timezone.now()
        self.anulada_por = usuario
        self.save()

# ITEMS DE LA VENTA

class VentaItem(models.Model):
    venta = models.ForeignKey(
        Venta,
        related_name="items",
        on_delete=models.CASCADE
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )

    cantidad = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
