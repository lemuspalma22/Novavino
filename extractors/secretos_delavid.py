import re
from datetime import datetime
from compras.models import Proveedor
from .extractor_base import ExtractorBase
from .utils_extractores import (
    extraer_folio,
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)


class ExtractorSecretosDeLaVid(ExtractorBase):
    def parse(self):
        proveedor, _ = Proveedor.objects.get_or_create(nombre="Secretos de la Vid S de RL de CV")

        folio = extraer_folio(self.text)
        uuid = extraer_uuid(self.text)
        fecha = extraer_fecha_emision(self.text)
        total = extraer_total(self.text)

        # Extraer productos
        productos = []
        
        # Estrategia mejorada: buscar bloques de productos entre líneas específicas
        # Formato típico:
        # Cantidad (4.0000)
        # Clave interna (POLI/ELI)
        # Descripción (POLI ELISIR LIMONE / LIMONCELLO)
        # %Desc (20.00)
        # P/U (366.2384)
        # Importe (1,464.95)
        # Unidad (pz)
        
        # Buscar la sección de productos (entre "FACTURA" y "Total")
        match_seccion = re.search(r"FACTURA.*?\n(.*?)\nTotal", self.text, re.DOTALL | re.IGNORECASE)
        if not match_seccion:
            # Fallback: buscar desde "Descripción" hasta "Total"
            match_seccion = re.search(r"Descripci[oó]n.*?\n(.*?)\nTotal", self.text, re.DOTALL | re.IGNORECASE)
        
        if match_seccion:
            seccion_productos = match_seccion.group(1)
            
            # Nuevo enfoque: los campos están en líneas separadas
            # Formato:
            # Línea 1: Cantidad (30.000 o 6.0000)
            # Línea 2: Clave (LEON/17)
            # Línea 3: Descripción (LEONE DE CASTRIS ILLIVIA Primitivo 100%)
            # Línea 4: %Desc (20.00)
            # Línea 5: P/U (218.0728)
            # Línea 6: Importe (6,542.18)
            # Línea 7: Unidad (pz)
            # Líneas extras: códigos SAT (50202203, XBO)
            # Líneas de impuestos (IEPS:..., IVA:...)
            
            # Enfoque más robusto: buscar por bloques terminados en "pz" o "PZ"
            # Luego extraer campos de forma más flexible
            
            # Primero, encontrar todos los bloques que terminan con la unidad "pz/PZ"
            # seguido de código SAT
            bloques_patron = r"(\d+\.\d{3,4})\s+.*?(pz|PZ)\s+\d{8}"
            
            for bloque_match in re.finditer(bloques_patron, seccion_productos, re.DOTALL | re.IGNORECASE):
                bloque_texto = bloque_match.group(0)
                
                # Extraer campos individuales del bloque
                # Cantidad: primer número con 3-4 decimales
                cantidad_match = re.search(r"(\d+\.\d{3,4})", bloque_texto)
                if not cantidad_match:
                    continue
                
                cantidad_str = cantidad_match.group(1)
                
                # Encontrar TODOS los números con decimales en el bloque
                todos_numeros = re.findall(r"([\d,]+\.\d{2,4})", bloque_texto)
                
                # El precio unitario suele ser el que tiene más decimales (4) después de la cantidad
                # O el segundo/tercer número considerable (>10)
                precio_str = None
                for num in todos_numeros:
                    num_limpio = num.replace(",", "")
                    try:
                        valor = float(num_limpio)
                        # El precio unitario suele estar entre 10 y 10,000
                        # y no es igual a la cantidad
                        if valor > 10 and num_limpio != cantidad_str:
                            # Preferir números con 4 decimales
                            if '.' in num and len(num.split('.')[1]) == 4:
                                precio_str = num
                                break
                    except:
                        continue
                
                # Si no encontramos uno con 4 decimales, tomar el primero >10 que no sea la cantidad
                if not precio_str:
                    for num in todos_numeros:
                        num_limpio = num.replace(",", "")
                        try:
                            valor = float(num_limpio)
                            if valor > 10 and num_limpio != cantidad_str:
                                precio_str = num
                                break
                        except:
                            continue
                
                if not precio_str:
                    continue
                
                # Clave interna: código alfanumérico con / o -
                clave_match = re.search(r"\b([A-Z0-9/\-]+)\b", bloque_texto)
                
                # Descripción: la línea después de la clave (o primera línea con texto largo)
                lineas = bloque_texto.split('\n')
                descripcion = ""
                clave_texto = clave_match.group(1) if clave_match else ""
                
                # Buscar la línea con la clave y tomar las siguientes líneas (puede ser multilínea)
                encontre_clave = False
                partes_descripcion = []
                for i, linea in enumerate(lineas):
                    linea_limpia = linea.strip()
                    
                    if clave_texto and linea_limpia == clave_texto:
                        # Encontramos la clave, tomar las siguientes líneas con texto
                        encontre_clave = True
                        continue
                    
                    if encontre_clave:
                        # Tomar líneas que tengan texto significativo
                        if len(linea_limpia) > 5 and re.search(r'[A-Za-z]', linea_limpia):
                            # Asegurar que no sea un código o número puro
                            if not linea_limpia.startswith('50202') and not re.fullmatch(r'[\d\.,\s]+', linea_limpia):
                                # Detener si encontramos el porcentaje de descuento (e.g., "20.00")
                                if re.fullmatch(r'\d{2}\.\d{2}', linea_limpia):
                                    break
                                partes_descripcion.append(linea_limpia)
                                # Si ya tenemos texto significativo (>15 chars), no agregar más
                                if len(' '.join(partes_descripcion)) > 30:
                                    break
                        # Si encontramos línea vacía o solo números, detener
                        elif len(partes_descripcion) > 0 and (not linea_limpia or re.fullmatch(r'[\d\.,\s]+', linea_limpia)):
                            break
                
                # Unir las partes de la descripción
                if partes_descripcion:
                    descripcion = ' '.join(partes_descripcion)
                    # Limpiar posibles artefactos pegados:
                    # - 'TRES RIBERAS "HA PASADO UN ÁNGEL" SEMIDU20.00' -> 'TRES RIBERAS "HA PASADO UN ÁNGEL"'
                    # Primero buscar palabra pegada con números: SEMIDU20.00
                    descripcion = re.sub(r'[A-Z]{2,}\d{1,2}\.\d{2}$', '', descripcion).strip()
                    # Luego eliminar espacios + números al final: 20.00
                    descripcion = re.sub(r'\s+\d{1,2}\.\d{2}$', '', descripcion).strip()
                    # Eliminar palabras sueltas en mayúsculas al final (restos)
                    descripcion = re.sub(r'\s+[A-Z]{2,10}$', '', descripcion).strip()
                
                # Si no encontramos después de la clave, buscar cualquier línea larga con texto
                if not descripcion:
                    for linea in lineas:
                        linea_limpia = linea.strip()
                        if len(linea_limpia) > 15 and re.search(r'[A-Za-z]{3,}', linea_limpia):
                            if linea_limpia != clave_texto and not linea_limpia.startswith('50202'):
                                if not re.fullmatch(r'[\d\.,\s]+', linea_limpia):
                                    descripcion = linea_limpia
                                    break
                
                if not descripcion:
                    descripcion = clave_texto if clave_texto else "PRODUCTO SIN NOMBRE"
                
                # Aplicar limpieza final a TODAS las descripciones (sin importar su origen)
                # - Eliminar SOLO texto pegado con números al final: SEMIDU20.00 -> nada
                # - Usar \S para evitar eliminar palabras válidas separadas por espacio
                descripcion = re.sub(r'\S*[A-Z]{3,}\d{1,2}\.\d{2}$', '', descripcion).strip()
                # - Eliminar números sueltos al final si quedaron: " 20.00"
                descripcion = re.sub(r'\s+\d{1,2}\.\d{2}$', '', descripcion).strip()
                
                try:
                    cantidad = float(cantidad_str)
                    precio_extraido = float(precio_str.replace(",", ""))
                    
                    # Calcular precio final con impuestos y descuento
                    # El precio en el PDF está sin impuestos ni descuento
                    # Aplicamos: IEPS 26.5% + IVA 16% - Descuento 24%
                    precio_unitario = precio_extraido * 1.265 * 1.16 * 0.76
                    
                    productos.append({
                        "nombre_detectado": descripcion,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unitario
                    })
                except ValueError:
                    continue

        # Extraer campos de IEPS para validación de descuentos
        ieps_1 = self._extraer_ieps(1)
        ieps_2 = self._extraer_ieps(2)
        ieps_3 = self._extraer_ieps(3)

        return {
            "uuid": uuid,
            "folio": folio,
            "fecha": fecha,
            "total": total,
            "proveedor": proveedor,
            "productos": productos,
            "ieps_1_tasa": 26.5,
            "ieps_1_importe": ieps_1,
            "ieps_2_tasa": 30.0,
            "ieps_2_importe": ieps_2,
            "ieps_3_tasa": 53.0,
            "ieps_3_importe": ieps_3,
        }
    
    def _extraer_ieps(self, numero):
        """Extrae el importe de IEPS 1, 2 o 3 del texto."""
        # Formato variado en diferentes facturas:
        # Formato 1 (inline): I.E.P.S. 1  26.5%  $1,560.53
        # Formato 2 (tabla visual que se extrae en múltiples líneas):
        #   En PDF visual:
        #     I.E.P.S. 1  26.5%    673.90
        #     I.E.P.S. 2  30%        0.00  
        #     I.E.P.S. 3  53%      885.13
        #   Pero al extraer texto se separa en líneas independientes
        
        # Intentar formato inline primero (valor en misma línea que la etiqueta)
        patron_inline = rf"I\.E\.P\.S\.\s*{numero}\s+[\d.]+%[\s:$]*([0-9,]+\.\d{{2}})"
        match = re.search(patron_inline, self.text, re.IGNORECASE)
        if match:
            importe_str = match.group(1).replace(",", "")
            try:
                return float(importe_str)
            except ValueError:
                pass
        
        # Formato multilinea: Los IEPS aparecen en orden 3→2→1 en el PDF
        # Ejemplo real de factura 2334:
        #   I.E.P.S. 3    53%
        #   I.E.P.S. 2    30%
        #   I.E.P.S. 1  26.5%
        #   Subtotal
        #   ...
        #   Descuento
        #   0.00      ← IEPS 2 (30%)
        #   673.90    ← IEPS 1 (26.5%)
        #   885.13    ← IEPS 3 (53%)
        patron_tabla = r"I\.E\.P\.S\.\s*3\s+53%.*?I\.E\.P\.S\.\s*2\s+30%.*?I\.E\.P\.S\.\s*1\s+26\.5%.*?Descuento\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
        match_tabla = re.search(patron_tabla, self.text, re.DOTALL | re.IGNORECASE)
        if match_tabla:
            # Mapeo correcto basado en observación de factura real
            valores = {
                2: match_tabla.group(1),  # Primer valor después de Descuento = IEPS 2
                1: match_tabla.group(2),  # Segundo valor = IEPS 1
                3: match_tabla.group(3),  # Tercer valor = IEPS 3
            }
            if numero in valores:
                try:
                    return float(valores[numero].replace(",", ""))
                except ValueError:
                    pass
        
        return 0.0
