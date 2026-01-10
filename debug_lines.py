#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pdfminer.high_level import extract_text
import re

def debug_lines():
    text = extract_text('VBM041202DD1FB24554.pdf') or ''
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    
    print("=== LÍNEAS ALREDEDOR DE PRODUCTOS ===")
    
    # Buscar las líneas que contienen los productos
    for i, line in enumerate(lines):
        if '30.00' in line or 'V.T. ALTOTINTO' in line or '269.86' in line or '8,095.80' in line:
            print(f"Línea {i}: {repr(line)}")
            if i > 0:
                print(f"  -1: {repr(lines[i-1])}")
            if i < len(lines)-1:
                print(f"  +1: {repr(lines[i+1])}")
            print()

if __name__ == "__main__":
    debug_lines()
