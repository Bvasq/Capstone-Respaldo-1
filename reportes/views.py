from datetime import timedelta, date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, F, Q, DecimalField, ExpressionWrapper

from inventario.models import Producto, AlertaStock
from ventas.models import Venta, VentaItem


def duenio_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("No tienes permiso para ver esta sección.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@duenio_required
def index(request):
    """
    Dashboard de reportes principales del negocio.
    """

    hoy = timezone.now().date()
    hace_30 = hoy - timedelta(days=30)

    #ESTADO DE STOCK GENERAL
    productos = Producto.objects.filter(activo=True).order_by("nombre")

    def estado_stock(p):
        if p.stock <= p.stock_minimo:
            return "BAJO"
        if p.stock <= p.stock_minimo * 1.5:
            return "MEDIO"
        return "ALTO"

    listado = [
        {
            "producto": p,
            "estado": estado_stock(p),
        }
        for p in productos
    ]

    #VENTAS ÚLTIMOS 30 DÍAS
    ventas_30 = (
        Venta.objects
        .filter(
            fecha__date__gte=hace_30,
            fecha__date__lte=hoy,
        )
        .exclude(estado__iexact="ANULADA")
    )

    total_vendido_30 = ventas_30.aggregate(total=Sum("total"))["total"] or 0

    # COSTOS Y PRECIOS
    margen_expr = ExpressionWrapper(
        F("cantidad") * (F("precio_unitario") - F("producto__costo")),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    margen_30 = (
        VentaItem.objects.filter(venta__in=ventas_30)
        .aggregate(ganancia=Sum(margen_expr))
        .get("ganancia")
        or 0
    )

    # TOP 10 PRODUCTOS X 30 DIAS
    top = (
        VentaItem.objects.filter(venta__in=ventas_30)
        .values("producto__nombre")
        .annotate(
            cantidad_total=Sum("cantidad"),
            monto_total=Sum("subtotal"),
        )
        .order_by("-cantidad_total")[:10]
    )

    #PRODUCTOS CON STOCK CRÍTICO
    criticos = (
        Producto.objects.filter(
            activo=True,
            stock__lte=F("stock_minimo"),
            stock_minimo__gt=0,
        )
        .order_by("stock")
    )

    #SUGERENCIAS DE COMPRA
    sugerencias = (
        Producto.objects.filter(
            activo=True,
            stock__lte=F("stock_minimo"),
            stock_minimo__gt=0,
        )
        .annotate(
            vendido_30=Sum(
                "ventaitem__cantidad",
                filter=Q(
                    ventaitem__venta__fecha__date__gte=hace_30,
                )
                & ~Q(ventaitem__venta__estado__iexact="ANULADA"),
            )
        )
        .order_by("-vendido_30")
    )

    #ALERTAS DE STOCK CRÍTICO NO ATENDIDAS
    alertas = (
        AlertaStock.objects.filter(atendida=False)
        .select_related("producto")
        .order_by("-creado_en")[:20]
    )

    # RANGO PARA EL SELECTOR X 30 DIAS
    inicio_rango = hoy - timedelta(days=29)

    fecha_str = request.GET.get("fecha_ganancia")

    try:
        if fecha_str:
            fecha_seleccionada = date.fromisoformat(fecha_str)
        else:
            fecha_seleccionada = hoy
    except ValueError:
        fecha_seleccionada = hoy

    # VALIDACION DEL RANGO DE LAS FECHAS
    if fecha_seleccionada < inicio_rango or fecha_seleccionada > hoy:
        fecha_seleccionada = hoy

    # VENTAS X DIA
    ventas_dia = (
        Venta.objects
        .filter(fecha__date=fecha_seleccionada)
        .exclude(estado__iexact="ANULADA")
    )

    items_dia = VentaItem.objects.filter(venta__in=ventas_dia)

    margen_dia_expr = ExpressionWrapper(
        F("cantidad") * (F("precio_unitario") - F("producto__costo")),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    ganancia_dia = (
        items_dia.aggregate(ganancia=Sum(margen_dia_expr)).get("ganancia") or 0
    )

    contexto = {
        "listado": listado,
        "total_vendido_30": total_vendido_30,
        "margen_30": margen_30,
        "top_productos": top,
        "criticos": criticos,
        "sugerencias": sugerencias,
        "alertas": alertas,
        "desde": hace_30,
        "hasta": hoy,
        "ganancia_dia": ganancia_dia,
        "fecha_ganancia": fecha_seleccionada,
        "inicio_rango_ganancia": inicio_rango,
        "fin_rango_ganancia": hoy,
    }

    return render(request, "reportes/index.html", contexto)
