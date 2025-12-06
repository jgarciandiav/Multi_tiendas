from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.dashboard_view, name='dashboard'),  # ← raíz redirige a dashboard
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),

    # Usuario
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/quitar/<int:item_id>/', views.quitar_del_carrito, name='quitar_del_carrito'),
    path('carrito/procesar/', views.procesar_compra, name='procesar_compra'),
    path('historial/', views.historial_compras, name='historial_compras'),
    path('orden/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
    path('orden/<int:orden_id>/pdf/', views.generar_pdf_orden, name='pdf_orden'),

    # Almacenero
    path('almacenero/', views.dashboard_almacenero, name='dashboard_almacenero'),
    path('almacenero/agregar/', views.agregar_producto_almacenero, name='agregar_producto_almacenero'),
    path('almacenero/editar/<int:producto_id>/', views.editar_producto_almacenero, name='editar_producto_almacenero'),

    # Administrador
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/productos-sin-precio/', views.admin_productos_sin_precio, name='admin_productos_sin_precio'),
    path('admin/asignar-precio/<int:producto_id>/', views.admin_asignar_precio, name='admin_asignar_precio'),
    path('admin/productos-vendidos/', views.admin_productos_vendidos, name='admin_productos_vendidos'),
    path('admin/gestion-usuarios/', views.admin_gestion_usuarios, name='admin_gestion_usuarios'),
    path('admin/crear-usuario/', views.admin_crear_usuario, name='admin_crear_usuario'),
    path('admin/desactivar/<int:user_id>/', views.admin_desactivar_usuario, name='admin_desactivar_usuario'),
    path('admin/actualizar-rol/<int:user_id>/', views.admin_actualizar_rol, name='admin_actualizar_rol'),
    path('admin/exportar-csv/', views.admin_exportar_csv, name='admin_exportar_csv'),
]