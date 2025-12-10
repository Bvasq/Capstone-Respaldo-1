from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True
    )

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos"
    )

    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Costo de compra del producto"
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de venta del producto"
    )

    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)

    activo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(
        default=False,
        help_text="Si está bloqueado, no puede venderse"
    )

    creado_en = models.DateTimeField(default=timezone.now)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def margen(self):
        """Retorna el margen bruto de ganancia."""
        try:
            return float(self.precio_unitario) - float(self.costo)
        except:
            return 0

    def __str__(self):
        return f"{self.sku} - {self.nombre}"
    

class AlertaStock(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="alertas"
    )
    creado_en = models.DateTimeField(default=timezone.now)
    atendida = models.BooleanField(default=False)
    mensaje = models.CharField(max_length=255)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Alerta {self.producto.nombre}: {self.mensaje}"
