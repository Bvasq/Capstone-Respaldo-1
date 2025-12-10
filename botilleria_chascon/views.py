from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import F
from inventario.models import Producto
from ventas.models import Trabajador, Turno, Venta
from django.db.models import Sum, Count
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from decimal import Decimal

def duenio_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("No tienes permiso para ver esta sección.")
        return view_func(request, *args, **kwargs)
    return wrapper


def inicio_general(request):
    return render(request, "inicio_general.html")


def landing(request):
    """
    Pantalla inicial de la app.
    SOLO muestra: logo grande + botón ADMIN + botón INICIO.
    Además, si hay productos con stock bajo, muestra un aviso.
    """
    # Limpia cuando inicia otra vez la app
    request.session.pop("modo_acceso", None)
    request.session.pop("es_admin", None)
    request.session.pop("trabajador_id", None)
    request.session.pop("turno_id", None)

    # Productos con stock crítico
    stock_bajo = Producto.objects.filter(
        activo=True,
        stock_minimo__gt=0,
        stock__lte=F("stock_minimo"),
    )

    contexto = {
        "hide_menu": True,
        "hay_stock_bajo": stock_bajo.exists(),
        "total_stock_bajo": stock_bajo.count(),
    }

    return render(request, "landing.html", contexto)

# ADMIN PASS X DEFECTO
ADMIN_PIN = "1234"


def admin_pin(request):
    """
    Vista donde el jefe ingresa su PIN.
    Si el PIN es correcto, se guarda en la sesión y pasa al menú admin.
    """
    if request.method == "POST":
        pin_ingresado = request.POST.get("pin")
        if pin_ingresado == ADMIN_PIN:
            request.session["es_admin"] = True
            request.session["modo_acceso"] = "admin"
            messages.success(request, "Acceso concedido.")
            return redirect("admin_menu")
        else:
            messages.error(request, "PIN incorrecto.")

    return render(request, "admin_pin.html", {"hide_menu": True})


def admin_menu(request):
    """
    Menú principal del administrador.
    Desde aquí accede a ventas, análisis, reportes, inventario y trabajadores.
    """
    if not request.session.get("es_admin"):
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect("admin_pin")

    return render(request, "admin_menu.html", {"hide_menu": True})

def cerrar_admin(request):
    """
    Cierra la sesión de administrador (PIN) y vuelve al inicio.
    """
    request.session.pop("es_admin", None)
    request.session.pop("modo_acceso", None)
    request.session.pop("trabajador_id", None)
    request.session.pop("turno_id", None)

    messages.success(request, "Sesión de administrador cerrada.")
    return redirect("landing")


def menu_admin(request):
    """
    Compatibilidad con código antiguo.
    Redirige al mismo menú de administrador, usando la lógica de PIN.
    """
    return admin_menu(request)


def inicio_limitado(request):
    """
    Vista antigua de 'inicio' modo vendedor.
    Ahora el flujo recomendado es usar 'inicio_trabajador' con turnos.
    """
    request.session["modo_acceso"] = "vendedor"
    return render(request, "menu_inicio.html")


#   TRABAJADORES DESDE EL ADMIN


@login_required
@duenio_required
def lista_trabajadores(request):
    # ESTO ES PARA CREAR TRABAJADORES NUEVES
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        turno_base = request.POST.get("turno_base")
        if nombre:
            Trabajador.objects.create(nombre=nombre, turno_base=turno_base)
        return redirect("lista_trabajadores")

    # LISTADO DE LOS TRABAJADORES
    trabajadores = Trabajador.objects.all().order_by("nombre")

    # VENTAS X TRABAJADOR
    estadisticas = (
        Venta.objects.filter(
            estado="CONFIRMADA",
            trabajador__isnull=False,
        )
        .values("trabajador_id", "trabajador__nombre")
        .annotate(
            trabajador_nombre=F("trabajador__nombre"),
            total_ventas=Count("id"),
            total_monto=Sum("total"),
        )
        .order_by("-total_monto")
    )

    context = {
        "trabajadores": trabajadores,
        "estadisticas": estadisticas,
    }
    return render(request, "trabajadores/lista_trabajadores.html", context)


def editar_trabajador(request, trabajador_id):
    if not request.session.get("es_admin"):
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect("admin_pin")

    trabajador = get_object_or_404(Trabajador, id=trabajador_id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        turno_base = request.POST.get("turno_base")

        if nombre and turno_base:
            trabajador.nombre = nombre
            trabajador.turno_base = turno_base
            trabajador.save()
            messages.success(request, "Trabajador actualizado correctamente.")
            return redirect("lista_trabajadores")
        else:
            messages.error(request, "Debe completar todos los campos.")

    context = {
        "trabajador": trabajador,
        "hide_menu": False,
    }
    return render(request, "trabajadores/editar_trabajador.html", context)


def eliminar_trabajador(request, trabajador_id):
    if not request.session.get("es_admin"):
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect("admin_pin")

    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    trabajador.activo = False
    trabajador.save()
    messages.success(request, "Trabajador eliminado (desactivado) correctamente.")
    return redirect("lista_trabajadores")


def obtener_o_crear_turno_activo(trabajador: Trabajador) -> Turno:
    """
    Busca si el trabajador ya tiene un turno activo hoy.
    Si no, crea uno nuevo automáticamente usando su turno_base.
    """
    hoy = timezone.localdate()
    turno = Turno.objects.filter(
        trabajador=trabajador,
        fecha=hoy,
        activo=True
    ).first()

    if not turno:
        turno = Turno.objects.create(
            trabajador=trabajador,
            fecha=hoy,
            hora_inicio=timezone.now(),
            turno_tipo=trabajador.turno_base,
            activo=True,
        )
    return turno


def inicio_trabajador(request):
    """
    Vista de INICIO (para trabajadores).
    - Muestra lista de trabajadores activos.
    - El trabajador selecciona su nombre y se inicia turno.
    - NO muestra menú admin.
    """
    trabajadores = Trabajador.objects.filter(activo=True)

    if request.method == "POST":
        trabajador_id = request.POST.get("trabajador_id")
        if trabajador_id:
            trabajador = get_object_or_404(Trabajador, id=trabajador_id, activo=True)
            turno = obtener_o_crear_turno_activo(trabajador)

            request.session["trabajador_id"] = trabajador.id
            request.session["turno_id"] = turno.id

            messages.success(request, f"Turno iniciado para {trabajador.nombre}.")
            return redirect("menu_trabajador") 
        else:
            messages.error(request, "Debe seleccionar un trabajador.")

    context = {
        "trabajadores": trabajadores,
        "hide_menu": True,
    }
    return render(request, "inicio_trabajador.html", context)


def menu_trabajador(request):
    """
    Menú para el trabajador:
    - Solo ver INVENTARIO y VENTAS.
    - NO tiene acceso a análisis, reportes ni trabajadores.
    """
    trabajador_id = request.session.get("trabajador_id")
    turno_id = request.session.get("turno_id")

    if not trabajador_id or not turno_id:
        messages.error(request, "No hay un turno activo. Debe iniciar turno primero.")
        return redirect("inicio_trabajador")

    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    turno = get_object_or_404(Turno, id=turno_id, activo=True)

    context = {
        "trabajador": trabajador,
        "turno": turno,
        "hide_menu": False,
    }
    return render(request, "menu_trabajador.html", context)


def cerrar_turno(request):
    """
    Cierra el turno actual del trabajador, registrando la hora de salida
    y limpiando la sesión.
    """
    trabajador_id = request.session.get("trabajador_id")
    turno_id = request.session.get("turno_id")

    if not trabajador_id or not turno_id:
        messages.error(request, "No hay turno activo para cerrar.")
        return redirect("inicio_trabajador")

    turno = get_object_or_404(Turno, id=turno_id, activo=True)
    turno.hora_fin = timezone.now()
    turno.activo = False
    turno.save()

    request.session.pop("trabajador_id", None)
    request.session.pop("turno_id", None)

    messages.success(request, "Turno cerrado correctamente.")
    return redirect("inicio")
