from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategorias'
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        if self.padre:
            return f"{self.padre} > {self.nombre}"
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # ← Puede ser NULL
    cantidad = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos')
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )
    fecha_vencimiento = models.DateField(null=True, blank=True)  # ← Para almacenero
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_creados')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_actualizados')

    # Para controlar visibilidad en el dashboard de usuario
    visible_para_usuario = models.BooleanField(default=False)

    @property
    def precio_total(self):
        if self.precio is None:
            return Decimal('0.00')
        return self.precio * self.cantidad

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nombre} (x{self.cantidad}) - S/{self.precio or 'Sin precio'}"

    def save(self, *args, **kwargs):
        # Si tiene precio, marcar como visible
        if self.precio is not None:
            self.visible_para_usuario = True
        else:
            self.visible_para_usuario = False
        super().save(*args, **kwargs)


# ===== MODELOS DE CARRO Y ORDEN (sin cambios) =====

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0

    @property
    def total_precio(self):
        return self.items.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('producto__precio'))
        )['total'] or Decimal('0.00')


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"
        unique_together = ('carrito', 'producto')

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def save(self, *args, **kwargs):
        if self.pk:
            anterior = ItemCarrito.objects.get(pk=self.pk)
            diff = self.cantidad - anterior.cantidad
            self._ajustar_stock(diff)
        else:
            self._ajustar_stock(self.cantidad)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._ajustar_stock(-self.cantidad)
        super().delete(*args, **kwargs)

    def _ajustar_stock(self, delta):
        producto = self.producto
        nuevo_stock = producto.cantidad - delta
        if nuevo_stock < 0:
            raise ValueError(f"No hay suficiente stock para '{producto.nombre}'. Disponible: {producto.cantidad}")
        producto.cantidad = nuevo_stock
        producto.save(update_fields=['cantidad'])


class Orden(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_creadas')

    class Meta:
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ['-fecha']

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario.username}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0


class ItemOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='items')
    producto_nombre = models.CharField(max_length=200)
    producto_id = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"

    def __str__(self):
        return f"{self.cantidad} x {self.producto_nombre}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario