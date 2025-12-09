from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("crear/", views.crear, name="crear"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("importar/", views.importar, name="importar"),
    path("plantilla.csv", views.plantilla_csv, name="plantilla"),
    path("categorias/", views.categorias_lista, name="categorias_lista"),
    path("categorias/crear/", views.categorias_crear, name="categorias_crear"),
    path("categorias/<int:pk>/editar/", views.categorias_editar, name="categorias_editar"),
    path("categorias/<int:pk>/eliminar/", views.categorias_eliminar, name="categorias_eliminar"),
]
