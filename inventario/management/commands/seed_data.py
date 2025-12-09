from datetime import timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from inventario.models import Categoria, Proveedor, Producto
from ventas.models import Venta, VentaItem


class Command(BaseCommand):
    help = "Genera datos de ejemplo para la Botillería El Chascón (categorías, productos y ventas)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Generando datos de ejemplo..."))

        User = get_user_model()
        user = User.objects.first()
        if not user:
            self.stdout.write(
                self.style.ERROR(
                    "No hay usuarios creados. Crea al menos un usuario con 'createsuperuser' antes de correr este comando."
                )
            )
            return

        categorias_nombres = ["Cervezas", "Vinos", "Licores", "Bebidas", "Snacks"]
        categorias = []

        for nombre in categorias_nombres:
            cat, _ = Categoria.objects.get_or_create(nombre=nombre)
            categorias.append(cat)

        proveedor, _ = Proveedor.objects.get_or_create(
            nombre="Distribuidora El Chascón",
            defaults={
                "telefono": "+56 9 1234 5678",
                "email": "contacto@elchascon.cl",
            },
        )

        if Producto.objects.count() == 0:
            self.stdout.write("No hay productos, creando productos de ejemplo...")

            productos_def = [
                ("CRN-001", "Cerveza Corona 330cc", "Cervezas", 800, 1200, 80, 20),
                ("ESC-001", "Cerveza Escudo 350cc", "Cervezas", 600, 1000, 60, 15),
                ("BUD-001", "Cerveza Budweiser 350cc", "Cervezas", 700, 1100, 50, 15),
                ("VIN-001", "Vino Gato Blanco 750cc", "Vinos", 1500, 2500, 30, 8),
                ("VIN-002", "Vino Gato Negro 750cc", "Vinos", 1500, 2600, 25, 8),
                ("PIS-001", "Pisco Mistral 35º 700cc", "Licores", 4500, 6500, 20, 5),
                ("RUM-001", "Ron Pampero 750cc", "Licores", 4000, 6200, 15, 4),
                ("BEB-001", "Bebida Coca-Cola 1.5L", "Bebidas", 900, 1500, 40, 10),
                ("BEB-002", "Bebida Sprite 1.5L", "Bebidas", 900, 1500, 35, 10),
                ("SNK-001", "Maní salado 100g", "Snacks", 300, 700, 50, 15),
            ]

            for sku, nombre, cat_nom, costo, precio, stock, stock_min in productos_def:
                cat = next(c for c in categorias if c.nombre == cat_nom)
                Producto.objects.create(
                    sku=sku,
                    nombre=nombre,
                    categoria=cat,
                    proveedor=proveedor,
                    costo=Decimal(costo),
                    precio_unitario=Decimal(precio),
                    stock=stock,
                    stock_minimo=stock_min,
                    activo=True,
                    bloqueado=False,
                )

        productos = list(Producto.objects.filter(activo=True, bloqueado=False))
        if not productos:
            self.stdout.write(self.style.ERROR("No hay productos activos para generar ventas."))
            return

        self.stdout.write("Creando ventas de los últimos 30 días...")

        hoy = timezone.now()
        dias = 30

        for i in range(dias):
            fecha_dia = hoy - timedelta(days=i)
            num_ventas = random.randint(0, 5)

            for _ in range(num_ventas):
                venta = Venta.objects.create(
                    fecha=fecha_dia,
                    usuario=user,
                    estado="CONFIRMADA",
                    total=Decimal("0"),
                )

                num_items = random.randint(1, 4)
                productos_venta = random.sample(productos, min(num_items, len(productos)))
                total_venta = Decimal("0")

                for prod in productos_venta:
                    if prod.stock <= 0:
                        continue

                    cantidad = random.randint(1, 5)
                    if prod.stock < cantidad:
                        cantidad = prod.stock

                    if cantidad == 0:
                        continue

                    subtotal = prod.precio_unitario * cantidad

                    VentaItem.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cantidad,
                        precio_unitario=prod.precio_unitario,
                        subtotal=subtotal,
                    )

                    prod.stock -= cantidad
                    prod.save()

                    total_venta += subtotal

                if total_venta == 0:
                    venta.delete()
                else:
                    venta.total = total_venta
                    venta.save()

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo generados con éxito."))
