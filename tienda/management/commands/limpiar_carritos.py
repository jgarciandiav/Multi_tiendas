from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from tienda.models import Carrito, ItemCarrito

class Command(BaseCommand):
    help = 'Limpia carritos abandonados (sin actividad en 24h) y devuelve el stock'

    def add_arguments(self, parser):
        parser.add_argument('--horas', type=int, default=24)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        horas = options['horas']
        dry_run = options['dry_run']
        limite = timezone.now() - timedelta(hours=horas)

        carritos = Carrito.objects.filter(
            items__isnull=False,
            items__agregado_en__lt=limite
        ).distinct()

        total_carritos = carritos.count()
        total_items = 0
        total_stock_devuelto = 0

        self.stdout.write(self.style.SUCCESS(f"🔍 Buscando carritos abandonados (> {horas}h)..."))

        for carrito in carritos:
            items = carrito.items.all()
            count_items = items.count()
            if count_items == 0:
                continue

            self.stdout.write(f"🧹 Carrito #{carrito.id} ({carrito.usuario.username}) → {count_items} item(s)")

            if not dry_run:
                with transaction.atomic():
                    for item in items:
                        producto = item.producto
                        producto.cantidad += item.cantidad
                        producto.save(update_fields=['cantidad'])
                        total_stock_devuelto += item.cantidad
                    items.delete()

            total_items += count_items

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Se limpiarían {total_items} items."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Limpieza: {total_items} items en {total_carritos} carritos. "
                f"Stock devuelto: {total_stock_devuelto}."
            ))