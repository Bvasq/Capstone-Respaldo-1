from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    # Django admin (no lo tocamos)
    path("admin/", admin.site.urls),

    # Pantalla inicial con logo + botones ADMIN / INICIO
    path("", views.landing, name="landing"),

    # Pantalla del PIN de seguridad (ADMIN)
    path("admin-pin/", views.admin_pin, name="admin_pin"),

    # Menú para dueño/admin (acceso total)
    path("admin-menu/", views.admin_menu, name="admin_menu"),
    path("admin-cerrar/", views.cerrar_admin, name="cerrar_admin"),

    # INICIO (TRABAJADOR): ahora usa la vista nueva con turnos
    # Este es el botón INICIO de la pantalla principal
    path("inicio/", views.inicio_trabajador, name="inicio"),

    # Menú del trabajador (solo VENTAS e INVENTARIO)
    path("menu-trabajador/", views.menu_trabajador, name="menu_trabajador"),

    # Cerrar turno del trabajador
    path("cerrar-turno/", views.cerrar_turno, name="cerrar_turno"),

    # Gestión de TRABAJADORES (solo ADMIN)
    path("trabajadores/", views.lista_trabajadores, name="lista_trabajadores"),
    path(
        "trabajadores/editar/<int:trabajador_id>/",
        views.editar_trabajador,
        name="editar_trabajador",
    ),
    path(
        "trabajadores/eliminar/<int:trabajador_id>/",
        views.eliminar_trabajador,
        name="eliminar_trabajador",
    ),

    # Apps de la botillería (las dejamos tal cual)
    path(
        "inventario/",
        include(("inventario.urls", "inventario"), namespace="inventario"),
    ),
    path(
        "ventas/",
        include(("ventas.urls", "ventas"), namespace="ventas"),
    ),
    path(
        "analisis/",
        include(("analisis.urls", "analisis"), namespace="analisis"),
    ),
    path(
        "reportes/",
        include(("reportes.urls", "reportes"), namespace="reportes"),
    ),
]
