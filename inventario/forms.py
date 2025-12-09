from django import forms
from .models import Producto, Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre"]

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["sku","nombre","categoria","costo_unitario","precio_venta","stock","stock_minimo","activo"]

class ImportCSVForm(forms.Form):
    archivo = forms.FileField(help_text="CSV con columnas: sku,nombre,categoria,costo_unitario,precio_venta,stock,stock_minimo,activo")