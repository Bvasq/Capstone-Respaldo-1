from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from inventario.models import Producto
from ventas.models import Venta, VentaItem

class ReportesViewsTests(TestCase):
    def setUp(self):
        self.prod1 = Producto.objects.create(
            sku="PROD-001",
            nombre="Cerveza Rubia",
            precio_unitario=Decimal("1000.00"),
            stock=20,
            categoria="cerveza",
            stock_minimo=2,
            activo=True,
        )
        self.prod2 = Producto.objects.create(
            sku="PROD-002",
            nombre="Vino Tinto",
            precio_unitario=Decimal("2500.00"),
            stock=15,
            categoria="vino",
            stock_minimo=2,
            activo=True,
        )

        self.venta = Venta.objects.create(total=Decimal("0"))
        VentaItem.objects.create(
            venta=self.venta,
            producto=self.prod1,
            cantidad=3,
            precio_unitario=self.prod1.precio_unitario,
        )
        VentaItem.objects.create(
            venta=self.venta,
            producto=self.prod2,
            cantidad=1,
            precio_unitario=self.prod2.precio_unitario,
        )

        self.venta.total = Decimal("3") * self.prod1.precio_unitario + Decimal("1") * self.prod2.precio_unitario
        self.venta.save(update_fields=["total"])

    def test_reporte_index_status(self):
        """
        Verifica que la vista principal de reportes cargue correctamente.
        """
        url = reverse("reportes:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reportes")

    def test_datos_reporte_existentes(self):
        """
        Comprueba que los datos de ventas creados se reflejen en el reporte.
        """
        url = reverse("reportes:index")
        response = self.client.get(url)
        self.assertContains
