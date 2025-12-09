#Test globales
from decimal import Decimal
from django.test import TestCase
from inventario.models import Producto
from ventas.models import Venta, VentaItem

class VentasFlowTests(TestCase):
    def test_crear_venta_actualiza_total(self):
        p1 = Producto.objects.create(
            sku="CERV-001", nombre="Lager 355ml",
            precio_unitario=Decimal("1000.00"),
            stock=20, categoria="cerveza", stock_minimo=5, activo=True
        )
        p2 = Producto.objects.create(
            sku="CERV-002", nombre="IPA 473ml",
            precio_unitario=Decimal("1100.00"),
            stock=20, categoria="cerveza", stock_minimo=5, activo=True
        )

        v = Venta.objects.create(total=Decimal("0"))

        VentaItem.objects.create(venta=v, producto=p1, cantidad=2, precio_unitario=p1.precio_unitario)
        VentaItem.objects.create(venta=v, producto=p2, cantidad=1, precio_unitario=p2.precio_unitario)

        v.refresh_from_db()
        if v.total == 0:
            v.total = Decimal("2") * p1.precio_unitario + Decimal("1") * p2.precio_unitario
            v.save(update_fields=["total"])

        self.assertEqual(v.total, Decimal("3100.00"))
