"""
Script para verificar si las variables de entorno están cargadas.
"""
import os
import dotenv

# Cargar .env explícitamente
print("\n" + "="*80)
print("VERIFICACION DE VARIABLES DE ENTORNO - VENTAS")
print("="*80)

# 1. Verificar que existe .env
print("\n[1/3] Verificando archivo .env...")
env_path = ".env"
if os.path.exists(env_path):
    print(f"  [OK] Archivo .env existe: {os.path.abspath(env_path)}")
    
    # Mostrar contenido relacionado con VENTAS
    print("\n  Contenido relacionado con VENTAS:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if 'VENTAS' in line.upper():
                print(f"    Línea {i}: {line.strip()}")
else:
    print(f"  [ERROR] Archivo .env NO existe en: {os.path.abspath(env_path)}")

# 2. Cargar variables explícitamente
print("\n[2/3] Cargando variables con dotenv.load_dotenv()...")
dotenv.load_dotenv(override=True)
print("  [OK] dotenv.load_dotenv() ejecutado")

# 3. Verificar variables
print("\n[3/3] Verificando variables en os.environ...")
required_vars = [
    'VENTAS_ROOT_ID',
    'VENTAS_NUEVAS_ID',
    'VENTAS_PROCESADAS_ID',
    'VENTAS_ERRORES_ID'
]

all_ok = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"  [OK] {var} = {value[:30]}...")
    else:
        print(f"  [ERROR] {var} = NO CONFIGURADA")
        all_ok = False

print("\n" + "="*80)
if all_ok:
    print("RESULTADO: ✅ Todas las variables están configuradas correctamente")
else:
    print("RESULTADO: ❌ Faltan variables")
    print("\nAGREGA ESTAS LINEAS A TU .env:")
    print("-"*80)
    print("VENTAS_ROOT_ID=1I6yGfo7qpq7Eb4T9KpqWnL4qKihbpwiZ")
    print("VENTAS_NUEVAS_ID=1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r")
    print("VENTAS_PROCESADAS_ID=19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v")
    print("VENTAS_ERRORES_ID=1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA")
    print("-"*80)

print("="*80 + "\n")
