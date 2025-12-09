from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from decimal import Decimal
from django.db.models import Q
from .forms import LoginForm, RegistroForm
from .models import Producto, Categoria, Carrito, ItemCarrito, Orden, ItemOrden
from django.contrib.auth.models import User, Group
import csv
from .models import LoginAttempt
#from tienda import models
from django.db.models import Q



# ===== DECORADORES DE ROL =====
def es_almacenero(user):
    return user.groups.filter(name='Almacenero').exists()


def es_admin(user):
    return user.groups.filter(name='Administrador').exists() or user.is_superuser


# ===== VISTAS DE AUTENTICACIÓN =====

def login_view(request):
    # Si ya está logueado, redirigir
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)  # ✅ Solo data=..., sin 'request'
        username = request.POST.get('username')

        # Verificar bloqueo por intentos fallidos
        if username:
            try:
                user = User.objects.get(username=username)
                attempt, _ = LoginAttempt.objects.get_or_create(user=user)
                
                if attempt.is_blocked():
                    tiempo_restante = (attempt.blocked_until - timezone.now()).total_seconds() // 60
                    messages.error(request, f"🔒 Tu cuenta está bloqueada por {int(tiempo_restante)} minutos por múltiples intentos fallidos.")
                    return render(request, 'login.html', {'form': form})
            except User.DoesNotExist:
                pass  # Usuario no existe → manejar como error normal

        # Procesar formulario
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Verificar bloqueo antes de login
                attempt, _ = LoginAttempt.objects.get_or_create(user=user)
                if attempt.is_blocked():
                    tiempo_restante = (attempt.blocked_until - timezone.now()).total_seconds() // 60
                    messages.error(request, f"🔒 Tu cuenta está bloqueada por {int(tiempo_restante)} minutos.")
                    return render(request, 'login.html', {'form': form})

                # Login exitoso → resetear intentos
                LoginAttempt.objects.filter(user=user).update(attempts=0, blocked_until=None)
                auth_login(request, user)
                messages.success(request, f"¡Bienvenido, {user.username}!")
                return redirect('dashboard')
            else:
                # Intento fallido → registrar
                if username:
                    try:
                        user = User.objects.get(username=username)
                        attempt, _ = LoginAttempt.objects.get_or_create(user=user)
                        attempt.add_attempt()
                        
                        if attempt.is_blocked():
                            messages.error(request, "🔒 Demasiados intentos fallidos. Tu cuenta está bloqueada por 2 horas.")
                        else:
                            mensajes_restantes = 5 - attempt.attempts
                            messages.error(request, f"Usuario o contraseña incorrectos. Te quedan {mensajes_restantes} intentos.")
                    except User.DoesNotExist:
                        messages.error(request, "Usuario o contraseña incorrectos.")
                else:
                    messages.error(request, "Por favor, ingresa un usuario.")
        else:
            messages.error(request, "Por favor, corrige los errores del formulario.")

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            nombre_completo = form.cleaned_data['nombre'].strip()
            partes = nombre_completo.split(' ', 1)
            first_name = partes[0]
            last_name = partes[1] if len(partes) > 1 else ''

            # ✅ PRIMERO: verificar si ya hay algún usuario (antes de crear el nuevo)
            tiene_usuarios = User.objects.exists()

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=first_name,
                last_name=last_name
            )

            # ✅ Ahora: si NO había usuarios antes, este es el PRIMERO
            if not tiene_usuarios:
                grupo_admin, _ = Group.objects.get_or_create(name='Administrador')
                user.groups.add(grupo_admin)
                #user.is_staff = True
                user.save()
                messages.success(request, f"¡Bienvenido, {user.username}! Eres el primer usuario. Rol: Administrador.")
            else:
                messages.success(request, f"¡Bienvenido, {user.username}! Tu cuenta ha sido creada como usuario.")

            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = RegistroForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect('login')


# ===== VISTA DE DASHBOARD (CON REDIRECCIÓN AUTOMÁTICA POR ROL) =====

@login_required
def dashboard_view(request):
    # ✅ Solo redirigir si NO hay parámetros de búsqueda/filtro
    if not request.GET:
        if es_admin(request.user):
            return redirect('admin_dashboard')
        elif es_almacenero(request.user):
            return redirect('dashboard_almacenero')

    # ✅ Si hay ?q=... o ?categoria=..., procesar aquí (usuario normal)
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')

    productos = Producto.objects.filter(
        cantidad__gt=0,
        visible_para_usuario=True
    )

    # Búsqueda
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        )

    # Filtro por categoría
    if categoria_id:
        try:
            categoria = Categoria.objects.get(id=categoria_id)
            if categoria.subcategorias.exists():
                productos = productos.filter(categoria__in=categoria.subcategorias.all())
            else:
                productos = productos.filter(categoria_id=categoria_id)
        except Categoria.DoesNotExist:
            pass

    productos = productos.order_by('-created_at')
    categorias = Categoria.objects.filter(padre__isnull=True)

    return render(request, 'dashboard.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_id,
        'q': q,
    })
# ===== VISTAS DE USUARIO (ROL: USUARIO) =====

@login_required
def obtener_o_crear_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
        defaults={'activo': True}
    )
    return carrito


@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, cantidad__gt=0, visible_para_usuario=True)
    carrito = obtener_o_crear_carrito(request)

    if request.method == "POST":
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1:
            messages.error(request, "La cantidad debe ser al menos 1.")
            return redirect('dashboard')
        if cantidad > producto.cantidad:
            messages.error(request, f"Solo hay {producto.cantidad} unidades disponibles.")
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


# ===== VISTAS DE ALMACENERO =====

@login_required
@user_passes_test(es_almacenero)
def dashboard_almacenero(request):
    productos = Producto.objects.all().order_by('-created_at')
    return render(request, 'almacenero/dashboard.html', {'productos': productos})


@login_required
@user_passes_test(es_almacenero)
def agregar_producto_almacenero(request):
    from .forms import ProductoForm
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.usuario = request.user
            producto.created_by = request.user
            producto.save()
            messages.success(request, f"✅ Producto '{producto.nombre}' agregado al almacén.")
            return redirect('dashboard_almacenero')
    else:
        form = ProductoForm()
    return render(request, 'almacenero/agregar_producto.html', {'form': form})


@login_required
@user_passes_test(es_almacenero)
def editar_producto_almacenero(request, producto_id):
    from .forms import ProductoForm
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.updated_by = request.user
            producto.save()
            messages.success(request, "✅ Producto actualizado.")
            return redirect('dashboard_almacenero')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'almacenero/editar_producto.html', {'form': form, 'producto': producto})


# ===== VISTAS DE ADMINISTRADOR =====

@login_required
@user_passes_test(es_admin)
def admin_dashboard(request):
    productos = Producto.objects.filter(precio__isnull=False, visible_para_usuario=True).order_by('-created_at')
    categorias = Categoria.objects.filter(padre__isnull=True)
    return render(request, 'admin/dashboard.html', {
        'productos': productos,
        'categorias': categorias,
    })


@login_required
@user_passes_test(es_admin)
def admin_productos_sin_precio(request):
    productos = Producto.objects.filter(precio__isnull=True).order_by('-created_at')
    return render(request, 'admin/productos_sin_precio.html', {'productos': productos})


@login_required
@user_passes_test(es_admin)
def admin_asignar_precio(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, precio__isnull=True)
    if request.method == "POST":
        precio = request.POST.get('precio')
        try:
            producto.precio = Decimal(precio)
            producto.save()
            messages.success(request, f"✅ Precio asignado a '{producto.nombre}': S/ {producto.precio}")
            return redirect('admin_productos_sin_precio')
        except Exception as e:
            messages.error(request, "Error al asignar precio. Asegúrate de usar formato decimal (ej: 24.00)")
    return render(request, 'admin/asignar_precio.html', {'producto': producto})


@login_required
@user_passes_test(es_admin)
def admin_productos_vendidos(request):
    fecha = request.GET.get('fecha')
    items = ItemOrden.objects.select_related('orden__usuario', 'orden')

    if fecha:
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            items = items.filter(orden__fecha__date=fecha_obj)
        except ValueError:
            messages.error(request, "Formato de fecha inválido. Usa YYYY-MM-DD")
            fecha = None

    from collections import defaultdict
    from decimal import Decimal
    resumen = defaultdict(lambda: {
        'cantidad_total': 0,
        'importe_total': Decimal('0.00'),
        'ultima_venta': None,
        'categoria': '',
        'tipo': ''
    })

    for item in items:
        key = item.producto_nombre
        resumen[key]['cantidad_total'] += item.cantidad
        resumen[key]['importe_total'] += item.subtotal
        
        # ✅ Usa item.producto_id (NO item.producto)
        try:
            producto_original = Producto.objects.get(id=item.producto_id)
            if producto_original.categoria:
                resumen[key]['categoria'] = producto_original.categoria.nombre
                if producto_original.categoria.padre:
                    resumen[key]['tipo'] = producto_original.categoria.padre.nombre
        except Producto.DoesNotExist:
            # Producto eliminado → dejar campos vacíos
            pass

        if not resumen[key]['ultima_venta'] or item.orden.fecha > resumen[key]['ultima_venta']:
            resumen[key]['ultima_venta'] = item.orden.fecha

    resumen_list = [
        {
            'nombre': nombre,
            'categoria': data['categoria'],
            'tipo': data['tipo'],
            'cantidad_total': data['cantidad_total'],
            'precio_unitario': item.precio_unitario,  # ✅ Ya está en ItemOrden
            'importe_total': data['importe_total'],
            'ultima_venta': data['ultima_venta']
        }
        for nombre, data in resumen.items()
    ]

    total_cantidad = sum(item['cantidad_total'] for item in resumen_list)
    total_importe = sum(item['importe_total'] for item in resumen_list)

    return render(request, 'admin/productos_vendidos.html', {
        'items': resumen_list,
        'fecha': fecha,
        'total_cantidad': total_cantidad,
        'total_importe': total_importe
    })

@login_required
@user_passes_test(es_admin)
def admin_gestion_usuarios(request):
    usuarios = User.objects.filter(
        groups__name__in=['Administrador', 'Almacenero']
    ).distinct().prefetch_related('groups')
    return render(request, 'admin/gestion_usuarios.html', {'usuarios': usuarios})


@login_required
@user_passes_test(es_admin)
def admin_crear_usuario(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        if not username or not email or not password or not rol:
            messages.error(request, "Todos los campos son obligatorios.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Este nombre de usuario ya existe.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Este correo ya está registrado.")
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=username.split(' ')[0] if ' ' in username else username,
                    last_name=' '.join(username.split(' ')[1:]) if ' ' in username else ''
                )
                grupo, _ = Group.objects.get_or_create(name=rol)
                user.groups.add(grupo)
                messages.success(request, f"✅ Usuario '{username}' creado como {rol}.")
                return redirect('admin_gestion_usuarios')
            except Exception as e:
                messages.error(request, f"Error al crear usuario: {str(e)}")

    return render(request, 'admin/crear_usuario.html', {
        'roles': ['Administrador', 'Almacenero']
    })


@login_required
@user_passes_test(es_admin)
def admin_desactivar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.warning(request, "No puedes desactivar un superusuario.")
    else:
        user.is_active = False
        user.save()
        messages.success(request, f"✅ Usuario '{user.username}' desactivado.")
    return redirect('admin_gestion_usuarios')


@login_required
@user_passes_test(es_admin)
def admin_actualizar_rol(request, user_id):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        rol = data.get('rol')
        user = get_object_or_404(User, id=user_id)
        if rol in ['Administrador', 'Almacenero']:
            user.groups.clear()
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Rol inválido'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ===== PERFIL =====
@login_required
def mi_perfil(request):
    return render(request, 'mi_perfil.html', {'user': request.user})


@login_required
@user_passes_test(es_admin)
def admin_exportar_csv(request):
    """Exporta productos vendidos a CSV"""
    fecha = request.GET.get('fecha')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="productos_vendidos.csv"'

    writer = csv.writer(response)
    # Cabecera
    writer.writerow([
        'Producto',
        'Categoría',
        'Tipo',
        'Cantidad Total',
        'Precio Unitario',
        'Importe Total',
        'Última Venta'
    ])

    # Obtener los mismos datos que en admin_productos_vendidos
    items_query = ItemOrden.objects.select_related('orden')
    if fecha:
        from datetime import datetime
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            items_query = items_query.filter(orden__fecha__date=fecha_obj)
        except:
            pass

    # Agrupar (igual que en la vista principal)
    from collections import defaultdict
    from decimal import Decimal
    resumen = defaultdict(lambda: {
        'cantidad_total': 0,
        'importe_total': Decimal('0.00'),
        'ultima_venta': None,
        'categoria': '',
        'tipo': ''
    })

    for item in items_query:
        key = item.producto_nombre
        resumen[key]['cantidad_total'] += item.cantidad
        resumen[key]['importe_total'] += item.subtotal
        if not resumen[key]['ultima_venta'] or item.orden.fecha > resumen[key]['ultima_venta']:
            resumen[key]['ultima_venta'] = item.orden.fecha
            try:
                producto_original = Producto.objects.get(id=item.producto_id)
                if producto_original.categoria:
                    resumen[key]['categoria'] = producto_original.categoria.nombre
                    if producto_original.categoria.padre:
                        resumen[key]['tipo'] = producto_original.categoria.padre.nombre
            except:
                pass

    # Escribir filas
    for nombre, data in resumen.items():
        writer.writerow([
            nombre,
            data['categoria'],
            data['tipo'],
            data['cantidad_total'],
            f"S/ {data.get('precio_unitario', 0)}",
            f"S/ {data['importe_total']}",
            data['ultima_venta'].strftime('%Y-%m-%d') if data['ultima_venta'] else ''
        ])

    return response