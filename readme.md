🚀 MultiTiendas - Installation Guide
Guía para instalar y configurar MultiTiendas en una nueva máquina.

📋 Requisitos previos
	✅ Python 3.8+
	✅ PostgreSQL 12+
	
🛠️ Pasos de instalación

1. Crear entorno virtual
	bash

		python -m venv venv
                venv\Scripts\activate

2. Instalar dependencias

	pip install -r requirements.txt

3. Configurar base de datos PostgreSQL
	a) Crear base de datos y usuario:

		psql o pgAdminCREATE DATABASE ventas;

	b) Actualizar el fichero  .env :
		DB_NAME=nombre de la base de datos
		DB_USER=administrador de postgresql
		DB_PASSWORD=Contrasena del administrador de la base
		DB_HOST=localhost
		DB_PORT=5432

4. Aplicar migraciones

	python manage.py makemigrations
	python manage.py migrate

5. Ejecutar los siguientes comandos
	python manage.py crear_grupos
	python manage.py insertar_categorias
6. Crear superusuario

	python manage.py createsuperuser  # Sigue las instrucciones (usuario: admin, email: opcional, password: admin123)

7. Iniciar el servidor de desarrollo

python manage.py runserver

