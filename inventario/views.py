import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Categoria, Producto


def to_decimal(val):
    """Convierte strings como '1.234,5' o '1234.5' a Decimal seguro."""
    if val is None:
        return Decimal("0")
    s = str(val).strip()
    if s == "":
        return Decimal("0")
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")

from django.shortcuts import render
from django.db.models import F

from .models import Producto, Categoria


def lista(request):
    """
    Listado de productos con filtros por categoría y estado (activo/inactivo).
    """
    # PRINCIPAL QUERY
    productos = Producto.objects.select_related("categoria").all().order_by("nombre")

    # TODAS LAS CAT
    categorias = Categoria.objects.all().order_by("nombre")

    # FILTROS DEL GET
    categoria_id = request.GET.get("categoria", "todas")
    estado = request.GET.get("estado", "todos")

    # FILTRO X CATEGORIA
    if categoria_id and categoria_id != "todas":
        productos = productos.filter(categoria_id=categoria_id)

    # Filtro X ESTADO
    if estado == "activos":
        productos = productos.filter(activo=True)
    elif estado == "inactivos":
        productos = productos.filter(activo=False)

    contexto = {
        "productos": productos,
        "categorias": categorias,
        "categoria_seleccionada": categoria_id,
        "estado_seleccionado": estado,
    }
    return render(request, "inventario/lista.html", contexto)


@login_required
def crear(request):
    categorias = Categoria.objects.all().order_by("nombre")
    errores = []

    if request.method == "POST":
        sku = (request.POST.get("sku") or "").strip()
        nombre = (request.POST.get("nombre") or "").strip()
        categoria_id = request.POST.get("categoria")
        precio = to_decimal(request.POST.get("precio_unitario"))
        stock = int(request.POST.get("stock", 0) or 0)
        stock_minimo = int(request.POST.get("stock_minimo", 0) or 0)

        if not sku:
            errores.append("El SKU no puede estar vacío.")
        elif Producto.objects.filter(sku__iexact=sku).exists():
            errores.append(f"El SKU '{sku}' ya existe, usa uno distinto.")

        if not nombre:
            errores.append("El nombre no puede estar vacío.")

        categoria = None
        if categoria_id:
            try:
                categoria = Categoria.objects.get(pk=int(categoria_id))
            except (ValueError, Categoria.DoesNotExist):
                errores.append("La categoría seleccionada no existe.")
        else:
            errores.append("Debes seleccionar una categoría.")

        if stock_minimo > stock:
            errores.append("El stock mínimo no puede ser mayor al stock.")

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(
                request,
                "inventario/crear.html",
                {"categorias": categorias},
            )

        # CREAR PRODUCTO
        Producto.objects.create(
            sku=sku,
            nombre=nombre,
            categoria=categoria,
            precio_unitario=precio,
            stock=stock,
            stock_minimo=stock_minimo,
            activo=True,
        )
        messages.success(request, "Producto creado correctamente.")
        return redirect("inventario:lista")

    return render(
        request,
        "inventario/crear.html",
        {"categorias": categorias},
    )


@login_required
def editar(request, pk):
    p = get_object_or_404(Producto, pk=pk)
    categorias = Categoria.objects.all().order_by("nombre")
    errores = []

    if request.method == "POST":
        nuevo_sku = (request.POST.get("sku") or "").strip()
        nombre = (request.POST.get("nombre") or "").strip()
        categoria_id = request.POST.get("categoria")
        precio = to_decimal(request.POST.get("precio_unitario"))
        stock = int(request.POST.get("stock", 0) or 0)
        stock_minimo = int(request.POST.get("stock_minimo", 0) or 0)
        activo = bool(request.POST.get("activo"))

        # VALIDAR
        if not nuevo_sku:
            errores.append("El SKU no puede estar vacío.")
        elif Producto.objects.filter(sku__iexact=nuevo_sku).exclude(pk=p.pk).exists():
            errores.append(f"El SKU '{nuevo_sku}' ya está asignado a otro producto.")

        if not nombre:
            errores.append("El nombre no puede estar vacío.")

        categoria = None
        if categoria_id:
            try:
                categoria = Categoria.objects.get(pk=int(categoria_id))
            except (ValueError, Categoria.DoesNotExist):
                errores.append("La categoría seleccionada no existe.")
        else:
            errores.append("Debes seleccionar una categoría.")

        if stock_minimo > stock:
            errores.append("El stock mínimo no puede ser mayor al stock.")

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(
                request,
                "inventario/editar.html",
                {"p": p, "categorias": categorias},
            )

        # ACTUALIZAR EL PRODUCTO
        p.sku = nuevo_sku
        p.nombre = nombre
        p.categoria = categoria
        p.precio_unitario = precio
        p.stock = stock
        p.stock_minimo = stock_minimo
        p.activo = activo
        p.save()

        messages.success(request, "Producto actualizado correctamente.")
        return redirect("inventario:lista")

    # GET X CATEGORAI
    return render(
        request,
        "inventario/editar.html",
        {"p": p, "categorias": categorias},
    )


@login_required
def eliminar(request, pk):
    p = get_object_or_404(Producto, pk=pk)
    try:
        p.delete()
        messages.success(request, "Producto eliminado.")
    except ProtectedError:
        p.activo = False
        p.save(update_fields=["activo"])
        messages.warning(
            request,
            "No se puede eliminar porque tiene ventas asociadas. Se desactivó.",
        )
    return redirect("inventario:lista")


#ESTO ES PA RECIBIR LOS CSV

@login_required
def plantilla_csv(request):
    headers = ["sku", "nombre", "categoria", "precio_unitario", "stock", "stock_minimo", "activo"]
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="plantilla_inventario.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    return response


@login_required
def importar(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        content = request.FILES["archivo"].read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        creados, actualizados = 0, 0

        for row in reader:
            sku = (row.get("sku") or "").strip()
            if not sku:
                continue

            nombre = (row.get("nombre") or "").strip()
            cat_nombre = (row.get("categoria") or "").strip()

            categoria = None
            if cat_nombre:
                categoria, _ = Categoria.objects.get_or_create(nombre=cat_nombre)

            precio = to_decimal(row.get("precio_unitario"))
            stock = int(row.get("stock") or 0)
            stock_minimo = int(row.get("stock_minimo") or 0)
            activo = str(row.get("activo", "1")).lower() in ["1", "true", "sí", "si", "y", "yes"]

            obj, created = Producto.objects.update_or_create(
                sku=sku,
                defaults={
                    "nombre": nombre,
                    "categoria": categoria,
                    "precio_unitario": precio,
                    "stock": stock,
                    "stock_minimo": stock_minimo,
                    "activo": activo,
                },
            )
            if created:
                creados += 1
            else:
                actualizados += 1

        messages.success(
            request,
            f"Importación OK. Creados: {creados}, Actualizados: {actualizados}",
        )
        return redirect("inventario:lista")

    return render(request, "inventario/importar.html")
# GESTION DE LAS CATEGORIAS

@login_required
def categorias_lista(request):
    categorias = Categoria.objects.all().order_by("nombre")
    return render(request, "inventario/categoria_list.html", {
        "categorias": categorias,
    })



@login_required
def categorias_crear(request):
    """Crear nueva categoría sencilla (solo nombre)."""
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()

        if not nombre:
            messages.error(request, "El nombre no puede estar vacío.")
        elif Categoria.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, "Ya existe una categoría con ese nombre.")
        else:
            Categoria.objects.create(nombre=nombre)
            messages.success(request, "Categoría creada correctamente.")
            return redirect("inventario:categorias_lista")

    return render(request, "inventario/categoria_form.html")


@login_required
def categorias_editar(request, pk):
    """Editar una categoría existente."""
    cat = get_object_or_404(Categoria, pk=pk)

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()

        if not nombre:
            messages.error(request, "El nombre no puede estar vacío.")
        elif Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, "Ya existe otra categoría con ese nombre.")
        else:
            cat.nombre = nombre
            cat.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("inventario:categorias_lista")

    return render(
        request,
        "inventario/categoria_form.html",
        {"categoria": cat},
    )


@login_required
def categorias_eliminar(request, pk):
    """Eliminar categoría (solo si no tiene productos asociados)."""
    cat = get_object_or_404(Categoria, pk=pk)

    tiene_productos = Producto.objects.filter(categoria=cat).exists()

    if tiene_productos:
        messages.error(
            request,
            "No se puede eliminar la categoría porque tiene productos asociados.",
        )
    else:
        cat.delete()
        messages.success(request, "Categoría eliminada correctamente.")

    return redirect("inventario:categorias_lista")
