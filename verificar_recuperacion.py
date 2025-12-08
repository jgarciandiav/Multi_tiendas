import os
from pathlib import Path

def verificar_plantillas():
    print("🔍 Verificando plantillas de recuperación de contraseña...")
    
    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / 'tienda'/ 'templates' / 'registration'
    print(templates_dir)
    plantillas = [
        'password_reset_form.html',
        'password_reset_done.html',
        'password_reset_confirm.html',
        'password_reset_complete.html',
        'password_reset_email.html',  # opcional pero recomendado
        'password_reset_subject.txt'   # opcional
    ]
    
    todas_ok = True
    for plantilla in plantillas:
        ruta = templates_dir / plantilla
        if ruta.exists():
            print(f"✅ {plantilla}")
        else:
            print(f"❌ {plantilla} → No encontrado")
            todas_ok = False
    
    if todas_ok:
        print("\n✅ Todas las plantillas están en templates/registration/")
    else:
        print(f"\n⚠️  Faltan plantillas. Crea la carpeta '{templates_dir}' y añade los archivos.")
    
    return todas_ok

def verificar_urls():
    print("\n🔍 Verificando tienda/urls.py...")
    
    urls_path = Path(__file__).resolve().parent / 'tienda' / 'urls.py'
    if not urls_path.exists():
        print("❌ tienda/urls.py no encontrado")
        return False
    
    try:
        with open(urls_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        checks = [
            ("from django.contrib.auth import views as auth_views", "✅ auth_views importado"),
            ("template_name='registration/", "✅ template_name usado"),
            ("name='password_reset'", "✅ URL nombrada correctamente"),
        ]
        
        for buscar, mensaje in checks:
            if buscar in contenido:
                print(mensaje)
            else:
                print(f"❌ Falta: {buscar}")
                return False
        
        print("✅ urls.py configurado correctamente")
        return True
    
    except Exception as e:
        print(f"❌ Error al leer urls.py: {e}")
        return False

def verificar_settings():
    print("\n🔍 Verificando settings.py...")
    
    settings_path = Path(__file__).resolve().parent / 'multi_tiendas' / 'settings.py'
    if not settings_path.exists():
        print("❌ settings.py no encontrado")
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        if 'templates' in contenido.lower() and 'dir' in contenido.lower():
            print("✅ TEMPLATES.DIRS incluye 'templates/'")
            return True
        else:
            print("⚠️  Verifica que TEMPLATES['DIRS'] tenga [BASE_DIR / 'templates']")
            return False
    
    except Exception as e:
        print(f"❌ Error al leer settings.py: {e}")
        return False

if __name__ == "__main__":
    print("🛠️  Script de verificación: Recuperación de Contraseña")
    print("=" * 55)
    
    ok1 = verificar_plantillas()
    ok2 = verificar_urls()
    ok3 = verificar_settings()
    
    print("\n" + "=" * 55)
    if ok1 and ok2 and ok3:
        print("🎉 ¡Todo listo! La recuperación de contraseña debería usar tus plantillas.")
    else:
        print("🔧 Acción requerida: Corrige los errores marcados arriba.")