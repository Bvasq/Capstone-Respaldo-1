# Botillería El Chascón — Sprint 2 (Ventas)

## Novedades
- App **ventas** con página **Venta rápida**.
- Carrito en sesión (agregar, listar, vaciar).
- Finalizar venta: crea `Venta` y `VentaItem` y **descuenta stock**.
- Búsqueda de productos por nombre o SKU.

## Cómo actualizar desde Sprint 1
1. Activar venv e instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Crear migraciones y aplicar:
   ```bash
   python manage.py makemigrations inventario ventas
   python manage.py migrate
   ```
3. Ejecutar:
   ```bash
   python manage.py runserver
   ```
4. Ir a **/ventas/rapida/** o usar el menú "Venta".