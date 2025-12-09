import json
from decimal import Decimal

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from inventario.models import Producto, AlertaStock
from .models import Venta, VentaItem, Trabajador, Turno



@login_required
def rapida(request):
    """
    Vista principal de venta rápida.
    """
    return render(request, "ventas/rapida.html")


@require_GET
@login_required
def buscar_productos(request):
    """
    Busca productos activos y no bloqueados para el buscador en vivo.
    """
    q = request.GET.get("q", "").strip()

    productos = Producto.objects.filter(activo=True, bloqueado=False)

    if q:
        productos = productos.filter(nombre__icontains=q) | productos.filter(sku__icontains=q)

    data = [
        {
            "id": p.id,
            "sku": p.sku,
            "nombre": p.nombre,
            "precio": float(p.precio_unitario),
            "stock": p.stock,
        }
        for p in productos.order_by("nombre")[:20]
    ]

    return JsonResponse({"results": data})


def _crear_alerta_stock(producto):
    """
    Genera una alerta si el stock está bajo el mínimo.
    """
    if producto.stock <= producto.stock_minimo and producto.stock_minimo > 0:
        AlertaStock.objects.get_or_create(
            producto=producto,
            atendida=False,
            defaults={
                "mensaje": f"Stock crítico: {producto.stock} unidades (mínimo {producto.stock_minimo})"
            },
        )

@require_POST
@login_required
def confirmar_venta(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        items = payload.get("items", [])
        metodo_pago = payload.get("metodo_pago", "EFECTIVO")  # por si envías el método de pago desde el front

        if not items:
            return HttpResponseBadRequest("No se enviaron ítems en la venta.")

        # TRANSACCIÓN ATÓMICA
        with transaction.atomic():
            # Buscar trabajador y turno activos desde la sesión (si es un trabajador en turno)
            trabajador = None
            turno = None

            trabajador_id = request.session.get("trabajador_id")
            turno_id = request.session.get("turno_id")

            if trabajador_id:
                try:
                    trabajador = Trabajador.objects.get(id=trabajador_id)
                except Trabajador.DoesNotExist:
                    trabajador = None

            if turno_id:
                try:
                    turno = Turno.objects.get(id=turno_id)
                except Turno.DoesNotExist:
                    turno = None

            # Crear la venta asociando usuario (django), trabajador y turno
            # y guardando el método de pago SI el modelo lo tiene
            venta_kwargs = {
                "usuario": request.user,
                "trabajador": trabajador,
                "turno": turno,
            }

            # Si el modelo Venta tiene campo metodo_pago, lo seteamos (no rompe si no existe)
            if hasattr(Venta, "metodo_pago"):
                venta_kwargs["metodo_pago"] = metodo_pago

            venta = Venta.objects.create(**venta_kwargs)

            total = Decimal("0")

            for it in items:
                prod_id = it.get("id")
                cant = int(it.get("cantidad", 0))

                if cant <= 0:
                    return HttpResponseBadRequest("Cantidad inválida.")

                # Bloqueo de fila para evitar condiciones de carrera
                producto = Producto.objects.select_for_update().get(id=prod_id)

                # Reglas de negocio
                if not producto.activo:
                    return HttpResponseBadRequest(f"El producto {producto.nombre} está inactivo.")

                if producto.bloqueado:
                    return HttpResponseBadRequest(
                        f"El producto {producto.nombre} está bloqueado y no puede venderse."
                    )

                if producto.stock < cant:
                    return HttpResponseBadRequest(f"Stock insuficiente para {producto.nombre}.")

                precio = producto.precio_unitario
                subtotal = precio * cant

                # Crear ítem
                VentaItem.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cant,
                    precio_unitario=precio,
                    subtotal=subtotal,
                )

                # Actualizar stock
                producto.stock -= cant
                producto.save(update_fields=["stock"])

                # Generar alerta si corresponde
                _crear_alerta_stock(producto)

                total += subtotal

            venta.total = total
            venta.save(update_fields=["total"])

        # URL del ticket en TXT
        ticket_url = reverse("ventas:ticket_txt", args=[venta.id])

        return JsonResponse(
            {
                "ok": True,
                "venta_id": venta.id,
                "total": float(total),
                "ticket_url": ticket_url,
            }
        )

    except Producto.DoesNotExist:
        return HttpResponseBadRequest("Producto no encontrado.")

    except Exception as e:
        return HttpResponseBadRequest(str(e))

@login_required
def ticket_txt(request, venta_id):
    """
    Genera un ticket de compra en formato .txt tipo boleta,
    listo para abrir e imprimir.
    """
    venta = get_object_or_404(Venta, id=venta_id)
    items = VentaItem.objects.filter(venta=venta).select_related("producto")

    # Nombre del vendedor
    if venta.trabajador:
        vendedor = venta.trabajador.nombre
    elif venta.usuario:
        vendedor = venta.usuario.get_full_name() or venta.usuario.username
    else:
        vendedor = "Administrador"

    # Fecha local
    fecha_local = timezone.localtime(venta.fecha)
    fecha_str = fecha_local.strftime("%d-%m-%Y %H:%M")

    # Método de pago (si existe el campo en el modelo)
    if hasattr(venta, "get_metodo_pago_display"):
        metodo_pago = venta.get_metodo_pago_display()
    else:
        metodo_pago = "N/A"

    # Armado del ticket tipo boleta (40 caracteres aprox por línea)
    lines = []
    lines.append(" BOTILLERÍA EL CHASCÓN")
    lines.append(" Ticket de venta")
    lines.append("")
    lines.append(f" Fecha : {fecha_str}")
    lines.append(f" Venta : {venta.id}")
    lines.append(f" Vendedor: {vendedor}")
    lines.append(f" Pago  : {metodo_pago}")
    lines.append("-" * 40)
    lines.append(" Cant  Descripción           P.U.   Total")
    lines.append("-" * 40)

    for item in items:
        nombre = (item.producto.nombre or "")[:18]  # cortamos a 18 chars
        cantidad = item.cantidad
        precio = int(item.precio_unitario)
        subtotal = int(item.subtotal)

        # Ej: "  2  Coca Cola 1.5L      1200   2400"
        line = f"{cantidad:>4}  {nombre:<18} {precio:>5} {subtotal:>7}"
        lines.append(line)

    lines.append("-" * 40)
    lines.append(f"{'TOTAL:':<10}{int(venta.total):>30}")
    lines.append("")
    lines.append(" Gracias por su compra.")
    lines.append("")

    contenido = "\n".join(lines)

    # 🔽 AQUÍ EL CAMBIO: forzar descarga en vez de inline
    response = HttpResponse(contenido, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename=\"ticket_{venta.id}.txt\"'
    return response

@login_required
def anular_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "")
        venta.anular(request.user, motivo)
        messages.success(request, "La venta fue ANULADA y el stock fue actualizado.")
        return redirect("ventas_historial")

    return render(request, "ventas/anular.html", {"venta": venta})
