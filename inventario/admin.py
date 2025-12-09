from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("sku", "nombre", "categoria", "precio_unitario", "stock", "stock_minimo", "activo")
    search_fields = ("sku", "nombre", "categoria")
    list_filter = ("categoria", "activo")
