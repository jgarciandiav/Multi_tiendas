from django.db.models import Sum

def carrito_info(request):
    total_items = 0
    if request.user.is_authenticated:
        # ✅ Recalcular SIEMPRE desde la BD (no caché)
        carrito = getattr(request.user, 'carrito', None)
        if carrito:
            total_items = carrito.items.aggregate(
                total=Sum('cantidad')
            )['total'] or 0
    return {'carrito_total_items': total_items}