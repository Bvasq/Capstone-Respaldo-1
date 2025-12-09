from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    # 👉 Ruta principal de la app /ventas/ -> vista rapida
    path("", views.rapida, name="rapida"),

    # 👉 Si quieres también que /ventas/rapida/ funcione:
    path("rapida/", views.rapida, name="rapida_alt"),

    # Endpoint AJAX para buscar productos
    path("buscar/", views.buscar_productos, name="buscar"),

    # Endpoint para confirmar la venta (JSON)
    path("confirmar/", views.confirmar_venta, name="confirmar"),

    # Ticket TXT (si ya implementaste esto antes)
    path("ticket/<int:venta_id>/txt/", views.ticket_txt, name="ticket_txt"),
]
