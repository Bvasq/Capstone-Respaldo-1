# tests global
from decimal import Decimal
from inventario.models import Producto
from ventas.models import Venta, VentaItem

def crear_producto(**kwargs):
    defaults = dict(
        sku="SKU-001",
        nombre="Producto genérico",
        precio_unitario=Decimal("1000.00"),
        stock=10,
        categoria="general",
        stock_minimo=1,
        activo=True,
    )
    defaults.update(kwargs)
    return Producto.objects.create(**defaults)

def crear_venta_con_items(items):
    v = Venta.objects.create(total=Decimal("0"))
    total = Decimal("0")
    for prod, cant in items:
        VentaItem.objects.create(
            venta=v,
            producto=prod,
            cantidad=cant,
            precio_unitario=prod.precio_unitario,
        )
        total += Decimal(cant) * prod.precio_unitario
    v.total = total
    v.save(update_fields=["total"])
    return v
