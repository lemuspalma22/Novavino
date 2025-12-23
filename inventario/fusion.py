"""
Funciones para fusión de productos duplicados.
Sistema de Fusión Suave: los productos no se eliminan, solo se marcan como fusionados.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Producto, AliasProducto, LogFusionProductos


def validar_fusion(producto_principal, producto_secundario):
    """
    Validaciones antes de permitir fusión.
    
    Returns:
        tuple: (es_valido: bool, errores: list, advertencias: list)
    """
    errores = []
    advertencias = []
    
    # 1. No fusionar consigo mismo
    if producto_principal.id == producto_secundario.id:
        errores.append("No puedes fusionar un producto consigo mismo")
    
    # 2. El producto secundario debe estar activo
    if not producto_secundario.activo:
        if producto_secundario.fusionado_en:
            errores.append(
                f"'{producto_secundario.nombre}' ya está fusionado en "
                f"'{producto_secundario.fusionado_en.nombre}'"
            )
        else:
            errores.append(f"'{producto_secundario.nombre}' no está activo")
    
    # 3. El producto principal debe estar activo
    if not producto_principal.activo:
        errores.append(f"'{producto_principal.nombre}' no está activo")
    
    # 4. No crear ciclos (A fusionado en B, B fusionado en A)
    if producto_principal.fusionado_en == producto_secundario:
        errores.append("No puedes crear ciclos de fusión")
    
    # 5. Advertencia si tienen categorías diferentes
    if producto_principal.tipo != producto_secundario.tipo:
        advertencias.append(
            f"ADVERTENCIA: Tipos diferentes "
            f"({producto_principal.tipo or 'sin tipo'} vs {producto_secundario.tipo or 'sin tipo'})"
        )
    
    # 6. Advertencia si tienen proveedores diferentes
    if producto_principal.proveedor_id != producto_secundario.proveedor_id:
        advertencias.append(
            f"ADVERTENCIA: Proveedores diferentes "
            f"({producto_principal.proveedor.nombre} vs {producto_secundario.proveedor.nombre})"
        )
    
    # 7. Advertencia si tienen precios muy diferentes
    if producto_principal.precio_venta and producto_secundario.precio_venta:
        diff_pct = abs(producto_principal.precio_venta - producto_secundario.precio_venta) / producto_principal.precio_venta * 100
        if diff_pct > 20:  # Más de 20% de diferencia
            advertencias.append(
                f"ADVERTENCIA: Precios de venta muy diferentes "
                f"(${producto_principal.precio_venta} vs ${producto_secundario.precio_venta})"
            )
    
    es_valido = len(errores) == 0
    return es_valido, errores, advertencias


def fusionar_productos_suave(producto_principal, producto_secundario, usuario, 
                             transferir_alias=True, razon=""):
    """
    Fusiona producto_secundario en producto_principal.
    Fusión Suave: el producto secundario se marca como inactivo pero no se elimina.
    
    Args:
        producto_principal: Producto que quedará activo
        producto_secundario: Producto que se marcará como inactivo
        usuario: Usuario que realiza la fusión
        transferir_alias: Si True, crea alias del nombre secundario
        razon: Razón de la fusión (opcional)
    
    Returns:
        dict con resultado de la operación:
            {
                'success': bool,
                'stock_transferido': int,
                'alias_creado': bool,
                'log_id': int,
                'errores': list,
                'advertencias': list
            }
    """
    # Validar
    es_valido, errores, advertencias = validar_fusion(producto_principal, producto_secundario)
    
    if not es_valido:
        return {
            'success': False,
            'errores': errores,
            'advertencias': advertencias
        }
    
    try:
        with transaction.atomic():
            # 1. Transferir stock
            stock_transferido = producto_secundario.stock or 0
            producto_principal.stock = (producto_principal.stock or 0) + stock_transferido
            
            # 2. Marcar secundario como fusionado
            producto_secundario.activo = False
            producto_secundario.fusionado_en = producto_principal
            producto_secundario.fecha_fusion = timezone.now()
            producto_secundario.stock = 0  # Stock se transfirió
            
            # 3. Crear alias del nombre secundario
            alias_creado = False
            if transferir_alias and producto_secundario.nombre:
                alias_obj, alias_creado = AliasProducto.objects.get_or_create(
                    alias=producto_secundario.nombre,
                    defaults={'producto': producto_principal}
                )
            
            # 4. Transferir aliases existentes del secundario al principal
            aliases_transferidos = AliasProducto.objects.filter(
                producto=producto_secundario
            ).update(
                producto=producto_principal
            )
            
            # 5. Log de auditoría
            log = LogFusionProductos.objects.create(
                producto_principal=producto_principal,
                producto_principal_nombre=producto_principal.nombre,
                producto_secundario_id=producto_secundario.id,
                producto_secundario_nombre=producto_secundario.nombre,
                stock_transferido=stock_transferido,
                usuario=usuario,
                razon=razon or "Productos duplicados"
            )
            
            # 6. Guardar cambios
            producto_secundario.save()
            producto_principal.save()
            
            return {
                'success': True,
                'stock_transferido': stock_transferido,
                'alias_creado': alias_creado,
                'aliases_transferidos': aliases_transferidos,
                'log_id': log.id,
                'errores': [],
                'advertencias': advertencias
            }
    
    except Exception as e:
        return {
            'success': False,
            'errores': [f"Error en transacción: {str(e)}"],
            'advertencias': advertencias
        }


def deshacer_fusion(producto_fusionado, restaurar_stock=True, usuario=None):
    """
    Revierte una fusión, reactivando el producto fusionado.
    
    Args:
        producto_fusionado: Producto que fue fusionado (activo=False)
        restaurar_stock: Si True, quitar stock del principal y devolverlo
        usuario: Usuario que deshace la fusión (opcional)
    
    Returns:
        dict con resultado:
            {
                'success': bool,
                'stock_restaurado': int,
                'error': str (si falló)
            }
    """
    if producto_fusionado.activo:
        return {
            'success': False,
            'error': 'Este producto no está fusionado'
        }
    
    if not producto_fusionado.fusionado_en:
        return {
            'success': False,
            'error': 'Producto inactivo pero sin fusión registrada'
        }
    
    try:
        with transaction.atomic():
            producto_principal = producto_fusionado.fusionado_en
            
            # Buscar log de fusión
            try:
                log = LogFusionProductos.objects.filter(
                    producto_principal=producto_principal,
                    producto_secundario_id=producto_fusionado.id,
                    revertida=False
                ).first()
                
                if log:
                    stock_a_restaurar = log.stock_transferido
                else:
                    stock_a_restaurar = 0
            except LogFusionProductos.DoesNotExist:
                stock_a_restaurar = 0
            
            # Restaurar stock si se solicita
            if restaurar_stock and stock_a_restaurar > 0:
                if producto_principal.stock >= stock_a_restaurar:
                    producto_principal.stock -= stock_a_restaurar
                    producto_fusionado.stock = stock_a_restaurar
                    producto_principal.save()
                else:
                    return {
                        'success': False,
                        'error': (
                            f"Stock insuficiente en '{producto_principal.nombre}' "
                            f"para restaurar (necesita {stock_a_restaurar}, tiene {producto_principal.stock})"
                        )
                    }
            
            # Reactivar producto
            producto_fusionado.activo = True
            producto_fusionado.fusionado_en = None
            producto_fusionado.fecha_fusion = None
            producto_fusionado.save()
            
            # Marcar log como revertido
            if log:
                log.revertida = True
                log.fecha_reversion = timezone.now()
                log.save()
            
            return {
                'success': True,
                'stock_restaurado': stock_a_restaurar if restaurar_stock else 0
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Error al deshacer fusión: {str(e)}"
        }


def fusionar_multiples_productos(producto_principal, productos_secundarios, usuario, razon=""):
    """
    Fusiona múltiples productos en uno solo.
    
    Args:
        producto_principal: Producto que quedará activo
        productos_secundarios: QuerySet o lista de productos a fusionar
        usuario: Usuario que realiza la fusión
        razon: Razón de la fusión
    
    Returns:
        dict con resumen:
            {
                'success': bool,
                'fusionados': int,
                'stock_total_transferido': int,
                'errores': list,
                'advertencias': list
            }
    """
    resultados = []
    stock_total = 0
    errores_globales = []
    advertencias_globales = []
    
    for secundario in productos_secundarios:
        resultado = fusionar_productos_suave(
            producto_principal,
            secundario,
            usuario,
            transferir_alias=True,
            razon=razon
        )
        
        resultados.append(resultado)
        
        if resultado['success']:
            stock_total += resultado['stock_transferido']
        else:
            errores_globales.extend(resultado.get('errores', []))
        
        advertencias_globales.extend(resultado.get('advertencias', []))
    
    fusionados_exitosos = sum(1 for r in resultados if r['success'])
    
    return {
        'success': fusionados_exitosos > 0,
        'fusionados': fusionados_exitosos,
        'intentados': len(productos_secundarios),
        'stock_total_transferido': stock_total,
        'errores': errores_globales,
        'advertencias': list(set(advertencias_globales))  # Remover duplicados
    }
