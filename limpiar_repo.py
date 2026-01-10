"""
Script de limpieza del repositorio - Elimina archivos temporales y obsoletos
"""
import os
import shutil
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent

# Categorías de archivos a eliminar
ARCHIVOS_ELIMINAR = {
    "Archivos vacíos": [
        "25.2",
        "backup.sql",
        "backup_local.sql",
    ],
    "PDFs de prueba": [
        "LEPR970522CD0_Factura_1106_E234D345-D60D-4576-9301-2EC0B1405A53.pdf",
        "LEPR970522CD0_Factura_1137_6AC32C47-863E-4E7E-85A5-0DD0F991AEB4.pdf",
        "VBM041202DD1FB25078.pdf",
    ],
    "Archivos ZIP": [
        "drive-download-20251112T021545Z-1-001.zip",
    ],
    "CSV temporales": [
        "inventario_prueba.csv",
        "productos_revision.csv",
        "productos_revision_corregido.csv",
    ],
    "TXT temporales": [
        "factura_1127_texto.txt",
        "productos_actualizacion_log.txt",
        "urls_novavino_prject.txt",
        "Instrucciones y comandos.txt",
    ],
    "Backups JSON": [
        "backup_inventario.json",
    ],
    "Scripts de corrección (obsoletos)": [
        "actualizar_mensaje_2335.py",
        "corregir_bacalauh.py",
        "corregir_epico.py",
        "corregir_factura_1116.py",
        "corregir_factura_1127.py",
        "corregir_factura_1137.py",
        "corregir_flags_ieps.py",
        "corregir_stock_duplicado.py",
        "limpiar_2334.py",
        "limpiar_alias_redundantes.py",
        "limpiar_flags_revisadas.py",
        "limpiar_pnr_huerfanos.py",
        "limpiar_y_reprocesar.py",
        "normalizar_proveedor_secretos_vid.py",
        "sincronizar_costos_transporte.py",
    ],
    "Scripts de debug (temporales)": [
        "analizar_diferencias_totales.py",
        "analizar_factura_1127.py",
        "analizar_factura_1137.py",
        "analizar_pdf_2445.py",
        "analizar_pnr.py",
        "debug_compra_904.py",
        "debug_drive_connection.py",
        "debug_encontrar_producto.py",
        "debug_epico.py",
        "debug_extractor.py",
        "debug_factura_1106.py",
        "debug_factura_1116.py",
        "debug_factura_25078.py",
        "debug_factura_904.py",
        "debug_fusion.py",
        "debug_ieps.py",
        "debug_lines.py",
        "debug_matching_25078.py",
        "debug_producto_perdido_2335.py",
        "diagnostico_1127_simple.py",
        "diagnostico_factura_1127.py",
        "investigar_asignacion_tres_riberas.py",
        "investigar_factura_2445.py",
        "revisar_factura_1116_db.py",
        "revisar_todos_productos.py",
        "verificar_2335.py",
        "verificar_2335_bd.py",
        "verificar_compra_2334.py",
        "verificar_costos_transporte.py",
        "verificar_env_ventas.py",
        "verificar_extraccion_1116.py",
        "verificar_extractor_cargado.py",
        "verificar_factura_1106_db.py",
        "verificar_flags.py",
        "verificar_flags_2334.py",
        "verificar_html_generado.py",
        "verificar_limpieza.py",
        "verificar_lineas_2335.py",
        "verificar_movimiento_archivos.py",
        "verificar_pnr_2445.py",
        "verificar_pnr_nombre_completo.py",
        "verificar_producto.py",
        "ver_texto_25078.py",
        "ver_texto_pdf.py",
        "ver_texto_pdf_ventas.py",
        "extraer_texto_1127.py",
        "leer_pdf_1127.py",
    ],
    "Scripts de procesamiento (obsoletos)": [
        "factura_parser.py",
        "reprocesar_factura_2445.py",
        "procesar_factura_2470_test.py",
        "simular_corte_1106.py",
        "reorganizar_carpetas_ventas_drive.py",
        "detectar_duplicados_ventas.py",
        "exportar_productos_revision.py",
        "importar_productos_corregidos.py",
        "importar_productos_corregidos_auto.py",
        "configurar_costos_transporte.py",
        "ejemplo_reporte_diferencias.py",
        "drive_connect.py",
        "generate_cut.py",
    ],
    "Tests obsoletos": [
        "test_fix_25078.py",
        "test_factura_1127.py",
        "test_factura_2335_regresion.py",
        "test_extractor_1127.py",
        "test_extraccion_completa_2334.py",
        "test_extractor_mejorado_2445.py",
        "test_fix_comillas.py",
        "test_validacion_directa.py",
        "test_vendor_extractor.py",
        "test_vb_no_roto.py",
        "test_limpieza_nombre.py",
        "test_validacion_precio.py",
    ],
}

DIRECTORIOS_ELIMINAR = [
    "__pycache__",
]


def contar_archivos():
    """Cuenta cuántos archivos se van a eliminar"""
    total = 0
    existentes = 0
    
    for categoria, archivos in ARCHIVOS_ELIMINAR.items():
        for archivo in archivos:
            total += 1
            filepath = BASE_DIR / archivo
            if filepath.exists():
                existentes += 1
    
    return total, existentes


def eliminar_archivos(dry_run=True):
    """Elimina los archivos especificados"""
    eliminados = []
    no_encontrados = []
    
    for categoria, archivos in ARCHIVOS_ELIMINAR.items():
        print(f"\n{'='*70}")
        print(f"📁 {categoria}")
        print(f"{'='*70}")
        
        for archivo in archivos:
            filepath = BASE_DIR / archivo
            
            if filepath.exists():
                size = filepath.stat().st_size
                size_kb = size / 1024
                
                print(f"  🗑️  {archivo} ({size_kb:.2f} KB)")
                
                if not dry_run:
                    try:
                        filepath.unlink()
                        eliminados.append(archivo)
                        print(f"      ✅ Eliminado")
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                else:
                    eliminados.append(archivo)
            else:
                no_encontrados.append(archivo)
                # print(f"  ⚠️  {archivo} - No encontrado")
    
    return eliminados, no_encontrados


def eliminar_pycache(dry_run=True):
    """Elimina todos los directorios __pycache__"""
    print(f"\n{'='*70}")
    print(f"📦 Eliminando directorios __pycache__")
    print(f"{'='*70}")
    
    eliminados = 0
    for pycache_dir in BASE_DIR.rglob("__pycache__"):
        print(f"  🗑️  {pycache_dir.relative_to(BASE_DIR)}")
        
        if not dry_run:
            try:
                shutil.rmtree(pycache_dir)
                eliminados += 1
                print(f"      ✅ Eliminado")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        else:
            eliminados += 1
    
    return eliminados


def main():
    print("\n" + "="*70)
    print("🧹 LIMPIEZA DEL REPOSITORIO")
    print("="*70)
    
    total, existentes = contar_archivos()
    
    print(f"\n📊 Resumen:")
    print(f"   Total de archivos en lista: {total}")
    print(f"   Archivos existentes: {existentes}")
    print(f"   Archivos ya eliminados: {total - existentes}")
    
    print("\n" + "="*70)
    print("MODO: SIMULACIÓN (dry-run)")
    print("="*70)
    print("Revisando qué se eliminaría...")
    
    eliminados, no_encontrados = eliminar_archivos(dry_run=True)
    pycache_count = eliminar_pycache(dry_run=True)
    
    print(f"\n{'='*70}")
    print(f"📊 RESULTADOS DE LA SIMULACIÓN")
    print(f"{'='*70}")
    print(f"  Archivos a eliminar: {len(eliminados)}")
    print(f"  Directorios __pycache__ a eliminar: {pycache_count}")
    print(f"  Total items a eliminar: {len(eliminados) + pycache_count}")
    
    print(f"\n{'='*70}")
    respuesta = input("\n¿Deseas EJECUTAR la limpieza real? (escribe 'SI' para confirmar): ")
    
    if respuesta.strip().upper() == "SI":
        print(f"\n{'='*70}")
        print("EJECUTANDO LIMPIEZA REAL...")
        print(f"{'='*70}")
        
        eliminados, no_encontrados = eliminar_archivos(dry_run=False)
        pycache_count = eliminar_pycache(dry_run=False)
        
        print(f"\n{'='*70}")
        print(f"✅ LIMPIEZA COMPLETADA")
        print(f"{'='*70}")
        print(f"  Archivos eliminados: {len(eliminados)}")
        print(f"  Directorios __pycache__ eliminados: {pycache_count}")
        print(f"\n🎉 ¡Repositorio limpio!")
        
        print(f"\n{'='*70}")
        print("📝 PRÓXIMOS PASOS:")
        print(f"{'='*70}")
        print("  1. Revisa los cambios con: git status")
        print("  2. Haz commit de los archivos eliminados")
        print("  3. Considera organizar la documentación en /docs/")
        print("  4. Actualiza el .gitignore si es necesario")
        
    else:
        print("\n❌ Limpieza cancelada.")


if __name__ == "__main__":
    main()
