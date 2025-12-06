@echo off
echo 🚀 Limpiando y reiniciando el proyecto MultiTiendas...

:: Detener servidor (si está corriendo en otra terminal, ignora el error)
taskkill /f /im python.exe 2>nul

:: Eliminar base de datos
if exist db.sqlite3 (
    echo 🗑️  Eliminando db.sqlite3...
    del db.sqlite3
) else (
    echo ⚠️  db.sqlite3 no existe. Continuando...
)

:: Eliminar migraciones personalizadas (solo las numeradas)
if exist tienda\migrations\ (
    echo 🧹 Eliminando migraciones antiguas...
    del /q tienda\migrations\0*.py 2>nul
    del /q tienda\migrations\0*.pyc 2>nul
)

:: Crear migraciones
echo 📦 Creando migraciones...
python manage.py makemigrations

:: Aplicar migraciones
echo 🔧 Aplicando migraciones...
python manage.py migrate

:: Crear grupos
echo 👥 Creando grupos de roles...
python manage.py crear_grupos

:: Mensaje final
echo ✅ ¡Listo! Proyecto reiniciado.
echo 🌐 Ejecuta: python manage.py runserver
pause