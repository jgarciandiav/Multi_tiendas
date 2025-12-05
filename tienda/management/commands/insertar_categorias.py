from django.core.management.base import BaseCommand
from tienda.models import Categoria

class Command(BaseCommand):
    help = 'Inserta categorías y subcategorías iniciales'

    def handle(self, *args, **options):
        Categoria.objects.all().delete()
        self.stdout.write(self.style.WARNING('⚠️  Categorías anteriores eliminadas.'))

        electro_hogar = Categoria.objects.create(
            nombre='Electrodomésticos y Artículos del hogar',
            descripcion='Productos para el hogar y electrodomésticos'
        )
        dulces_regalos = Categoria.objects.create(
            nombre='Dulces y Regalos',
            descripcion='Dulces, confituras y artículos de regalo'
        )
        juguetes = Categoria.objects.create(
            nombre='Juguetes',
            descripcion='Juguetes para todas las edades'
        )

        # Subcategorías — ¡nombres únicos!
        Categoria.objects.create(nombre='Electrodomésticos', descripcion='Lavadoras, refrigeradoras, etc.', padre=electro_hogar)
        Categoria.objects.create(nombre='Artículos de hogar', descripcion='Utensilios, decoración, limpieza', padre=electro_hogar)
        Categoria.objects.create(nombre='Dulces', descripcion='Chocolates, caramelos, galletas', padre=dulces_regalos)
        Categoria.objects.create(nombre='Confituras', descripcion='Mermeladas, jaleas, dulces tradicionales', padre=dulces_regalos)
        Categoria.objects.create(nombre='Regalos', descripcion='Peluches, cajas, artículos para regalo', padre=dulces_regalos)
        Categoria.objects.create(nombre='Juguetes Infantiles', descripcion='Juguetes educativos y de construcción', padre=juguetes)  # ← ¡CAMBIADO!

        self.stdout.write(self.style.SUCCESS('✅ Categorías y subcategorías insertadas correctamente.'))