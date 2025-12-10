from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.rapida, name="rapida"),
    path("rapida/", views.rapida, name="rapida_alt"),
    path("buscar/", views.buscar_productos, name="buscar"),
    path("confirmar/", views.confirmar_venta, name="confirmar"),
    path("ticket/<int:venta_id>/txt/", views.ticket_txt, name="ticket_txt"),
]
