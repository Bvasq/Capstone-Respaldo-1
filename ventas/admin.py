from django.contrib import admin
from .models import Venta, VentaItem


class VentaItemInline(admin.TabularInline):
    model = VentaItem
    extra = 0
    readonly_fields = ("producto", "cantidad", "precio_unitario", "subtotal")


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "usuario", "total", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("usuario__username",)
    readonly_fields = ("fecha", "usuario", "total", "estado")
    inlines = [VentaItemInline]


@admin.register(VentaItem)
class VentaItemAdmin(admin.ModelAdmin):
    list_display = ("id", "venta", "producto", "cantidad", "precio_unitario", "subtotal")
    list_filter = ("producto",)
    search_fields = ("producto__nombre",)
