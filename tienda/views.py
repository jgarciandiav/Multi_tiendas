from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from decimal import Decimal
from .forms import LoginForm
from .models import Producto, Categoria, Carrito, ItemCarrito, Orden, ItemOrden


@login_required
def mi_perfil(request):
    return render(request, 'mi_perfil.html', {'user': request.user})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def dashboard_view(request):
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = Producto.objects.filter(categoria_id=categoria_id, cantidad__gt=0)
    else:
        productos = Producto.objects.filter(cantidad__gt=0)

    categorias = Categoria.objects.filter(padre__isnull=True)
    return render(request, 'dashboard.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_id,
    })


@login_required
def obtener_o_crear_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
        defaults={'activo': True}
    )
    return carrito


@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, cantidad__gt=0)
    carrito = obtener_o_crear_carrito(request)

    if request.method == "POST":
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1:
            messages.error(request, "La cantidad debe ser al menos 1.")
            return redirect('dashboard')

        try:
            with transaction.atomic():
                item, creado = ItemCarrito.objects.get_or_create(
                    carrito=carrito,
                    producto=producto,
                    defaults={'cantidad': cantidad}
                )
                if not creado:
                    item.cantidad += cantidad
                    item.save()
                messages.success(request, f"✅ {producto.nombre} añadido al carrito.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, "Error al añadir al carrito.")

    return redirect('dashboard')


@login_required
def quitar_del_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)

    if request.method == "POST":
        try:
            with transaction.atomic():
                producto_nombre = item.producto.nombre
                cantidad_quitada = item.cantidad
                item.delete()
                messages.success(
                    request,
                    f"❌ {cantidad_quitada}x {producto_nombre} eliminado(s) del carrito."
                )
        except Exception as e:
            messages.error(request, "Error al quitar del carrito.")

    return redirect('ver_carrito')


@login_required
def ver_carrito(request):
    carrito = obtener_o_crear_carrito(request)
    items = carrito.items.select_related('producto').all()
    return render(request, 'carrito.html', {
        'carrito': carrito,
        'items': items,
    })


@login_required
def procesar_compra(request):
    carrito = obtener_o_crear_carrito(request)
    items = carrito.items.select_related('producto').all()

    if not items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')

    try:
        with transaction.atomic():
            total = carrito.total_precio
            orden = Orden.objects.create(
                usuario=request.user,
                total=total,
                created_by=request.user,
                estado='completada'
            )

            item_ordenes = []
            for item in items:
                item_ordenes.append(
                    ItemOrden(
                        orden=orden,
                        producto_nombre=item.producto.nombre,
                        producto_id=item.producto.id,
                        cantidad=item.cantidad,
                        precio_unitario=item.producto.precio
                    )
                )
            ItemOrden.objects.bulk_create(item_ordenes)

            carrito.items.all().delete()

            messages.success(request, f"✅ ¡Compra realizada! Orden #{orden.id} generada.")
            return redirect('detalle_orden', orden_id=orden.id)

    except Exception as e:
        messages.error(request, f"Error al procesar la compra: {str(e)}")
        return redirect('ver_carrito')


@login_required
def historial_compras(request):
    ordenes = Orden.objects.filter(
        usuario=request.user,
        estado='completada'
    ).prefetch_related('items')
    return render(request, 'historial.html', {'ordenes': ordenes})


@login_required
def detalle_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, usuario=request.user)
    return render(request, 'detalle_orden.html', {'orden': orden})


@login_required
def generar_pdf_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, usuario=request.user)

    template = get_template('pdf/orden_pdf.html')
    context = {
        'orden': orden,
        'fecha_hoy': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'empresa': {
            'nombre': 'MultiTiendas S.A.C.',
            'ruc': '12345678901',
            'direccion': 'Av. Comercio 123, Lima',
            'telefono': '+51 987 654 321',
        }
    }
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orden_{orden.id}.pdf"'

    pisa_status = pisa.CreatePDF(
        BytesIO(html.encode('UTF-8')),
        dest=response,
        encoding='UTF-8'
    )

    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=400)
    return response

@login_required
def mi_perfil(request):
    return render(request, 'mi_perfil.html', {'user': request.user})