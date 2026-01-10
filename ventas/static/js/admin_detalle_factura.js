// static/js/admin_detalle_factura.js
(function () {
    console.log("admin_detalle_factura.js ✅ cargado");
  
    // ---------- helpers ----------
    function toNum(v) {
      const n = parseFloat(String(v ?? "").replace(",", "."));
      return isNaN(n) ? 0 : n;
    }
  
    function isTemplateRow(row) {
      // La fila "plantilla" del formset tiene __prefix__ en los names
      return !!row.querySelector('[name*="__prefix__"]');
    }
  
    function isDetailRow(row) {
      if (!row || row.tagName !== "TR") return false;
      if (row.classList.contains("empty-form")) return false;
      if (isTemplateRow(row)) return false;
      // Consideramos fila válida si tiene alguno de estos campos
      return !!(
        row.querySelector('select[name$="producto"]') &&
        row.querySelector('input[name$="cantidad"]') &&
        row.querySelector('input[name$="precio_unitario"]')
      );
    }
  
    function findDetailRows() {
      return Array.from(document.querySelectorAll("tr"))
        .filter(isDetailRow);
    }
  
    function getRow(el) {
      let tr = el.closest("tr");
      return isDetailRow(tr) ? tr : null;
    }
  
    function qRowInputEndsWith(row, suffix) {
      return row ? row.querySelector('input[name$="' + suffix + '"]') : null;
    }
  
    function getProductoSelect(row) {
      return row ? row.querySelector('select[name$="producto"]') : null;
    }
  
    // ---------- cálculos ----------
    function getRowSubtotal(row) {
      const cantidad = toNum(qRowInputEndsWith(row, "cantidad")?.value);
      const precioUnit = toNum(qRowInputEndsWith(row, "precio_unitario")?.value);
      return cantidad * precioUnit;
    }
  
    function getTotalTargets() {
        const input = document.querySelector('input[name="total"], input[name$="total"]');
        const cell  = document.querySelector("td.field-total, .field-total");
        const label = document.querySelector("#total-display");
        const roBox   = document.querySelector(".field-total_display .readonly");
        return { input, cell, label, roBox };
      }
  
    function updateGrandTotal() {
      const { input, cell, label, roBox } = getTotalTargets();
  
      let grand = 0;
      findDetailRows().forEach((row) => {
        // omitir filas marcadas para borrar
        const del = row.querySelector('input[name$="-DELETE"]');
        if (del && del.checked) return;
        grand += getRowSubtotal(row);
      });
  
      const val = grand.toFixed(2);
      if (input && input.value !== val) input.value = val;
      if (cell  && cell.textContent !== val)  cell.textContent  = val;
      if (label && label.textContent !== val) label.textContent = val;
      if (roBox && roBox.textContent !== val) roBox.textContent = val;
    }
  
    function updateSubtotal(row) {
      if (!row) return;
      const val = getRowSubtotal(row).toFixed(2);
      const cell = row.querySelector("td.field-subtotal");
      if (cell) cell.textContent = val;
      else {
        const inp = qRowInputEndsWith(row, "subtotal");
        if (inp) inp.value = val;
      }
      updateGrandTotal();
    }
  
    // ---------- wiring ----------
    async function onProductoChange(e) {
      const row = getRow(e.target);
      if (!row) return;
      const id = e.target.value;
      if (!id) return;
  
      try {
        const r = await fetch(`${window.location.origin}/ventas/api/producto-precios/${id}/`, {
          credentials: "same-origin",
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
  
        const inpVenta  = qRowInputEndsWith(row, "precio_unitario");
        const inpCompra = qRowInputEndsWith(row, "precio_compra");
  
        if (inpVenta && !inpVenta.value && data.precio_venta != null) {
          inpVenta.value = Number(data.precio_venta).toFixed(2);
        }
        if (inpCompra && data.precio_compra != null) {
          inpCompra.value = Number(data.precio_compra).toFixed(2);
          // inpCompra.readOnly = true; // opcional
        }
  
        updateSubtotal(row);
      } catch (err) {
        console.error("No se pudieron cargar precios del producto:", err);
      }
    }
  
    function wireRow(row) {
      if (!isDetailRow(row) || row.dataset._wiredRow) return;
      row.dataset._wiredRow = "1";
  
      const sel = getProductoSelect(row);
      if (sel && !sel.dataset._wired) {
        sel.addEventListener("change", onProductoChange);
        sel.dataset._wired = "1";
      }
  
      ["cantidad", "precio_unitario"].forEach((suffix) => {
        const input = qRowInputEndsWith(row, suffix);
        if (input && !input.dataset._wired) {
          input.addEventListener("input", () => updateSubtotal(row));
          input.dataset._wired = "1";
        }
      });
  
      // Inicial (por si ya trae datos)
      updateSubtotal(row);
    }
  
    function wireAll() {
      findDetailRows().forEach(wireRow);
      updateGrandTotal();
    }
  
    function init() {
        wireAll();
    
        // 1) MutationObserver: solo filas NUEVAS, no re-wirear por cualquier cambio de texto
        const container =
          document.querySelector(".inline-group") || document.querySelector("fieldset") || document.body;
        const obs = new MutationObserver((muts) => {
          muts.forEach((m) => {
            m.addedNodes.forEach((node) => {
              if (node.nodeType !== 1) return;
              if (node.matches && node.matches("tr")) {
                if (isDetailRow(node)) wireRow(node);
              } else if (node.querySelectorAll) {
                node.querySelectorAll("tr").forEach((tr) => {
                  if (isDetailRow(tr)) wireRow(tr);
                });
              }
            });
          });
        });
        obs.observe(container, { childList: true, subtree: true });
    
        // 2) Evento formset de Django (si existe)
        document.body.addEventListener("formset:added", (e) => {
          const tr = e.target && e.target.closest ? e.target.closest("tr") : null;
          if (isDetailRow(tr)) wireRow(tr);
          updateGrandTotal();
        });
    
        // 3) Fallback: click en “Agregar otro/a Detalle factura”
        document.body.addEventListener("click", (ev) => {
          if (ev.target.closest && ev.target.closest(".add-row a")) {
            setTimeout(() => {
              findDetailRows().forEach(wireRow);
              updateGrandTotal();
            }, 0);
          }
        });
      }
  
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  })();
  