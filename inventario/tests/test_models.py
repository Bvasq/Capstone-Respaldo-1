#test para inventario
from decimal import Decimal
from django.test import TestCase
from inventario.models import Producto
from tests.factories import crear_producto


class ProductoModelTests(TestCase):
    def test_creacion_basica(self):
        p = crear_producto(sku="PY-001", nombre="Cerveza X", precio_unitario=1200, stock=7)
        self.assertIsInstance(p, Producto)
        self.assertTrue(p.activo)
        self.assertEqual(p.sku, "PY-001")
        self.assertEqual(p.precio_unitario, 1200)
        self.assertEqual(p.stock, 7)

    def test_precio_decimal_con_2_decimales(self):
        p = crear_producto(precio_unitario=Decimal("1234.50"))
        self.assertEqual(Decimal(p.precio_unitario), Decimal("1234.50"))

    def test_toggle_activo(self):
        p = crear_producto(activo=False)
        self.assertFalse(p.activo)
        p.activo = True
        p.save()
        p.refresh_from_db()
        self.assertTrue(p.activo)
