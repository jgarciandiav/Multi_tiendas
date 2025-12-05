from django.urls import path
from django.contrib.auth import views as auth_views  # 👈 ESTA LÍNEA ES LA CLAVE
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/quitar/<int:item_id>/', views.quitar_del_carrito, name='quitar_del_carrito'),
    path('carrito/procesar/', views.procesar_compra, name='procesar_compra'),
    path('historial/', views.historial_compras, name='historial_compras'),
    path('orden/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
    path('orden/<int:orden_id>/pdf/', views.generar_pdf_orden, name='pdf_orden'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
   
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]