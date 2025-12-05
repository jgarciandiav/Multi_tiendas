def carrito_info(request):
    total_items = 0
    if request.user.is_authenticated:
        carrito = getattr(request.user, 'carrito', None)
        if carrito:
            total_items = carrito.total_items
    return {'carrito_total_items': total_items}