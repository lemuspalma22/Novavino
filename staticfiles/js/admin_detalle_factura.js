document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("select[name$='producto']").forEach(function (selectProducto) {
        selectProducto.addEventListener("change", function () {
            const productoId = this.value; // Obtiene el ID del producto seleccionado
            const precioField = this.closest(".inline-related").querySelector("input[name$='precio_unitario']");
            const subtotalField = this.closest(".inline-related").querySelector("input[name$='subtotal']");
            const cantidadField = this.closest(".inline-related").querySelector("input[name$='cantidad']");

            if (productoId) {
                // Hacer una solicitud AJAX para obtener el precio del producto
                fetch(`/ventas/get_producto_precio/${productoId}/`)
                    .then(response => response.json())
                    .then(data => {
                        precioField.value = data.precio_unitario;
                        calcularSubtotal();
                    });
            }
        });
    });

    // Actualizar subtotal cuando se cambie la cantidad o precio unitario
    document.querySelectorAll("input[name$='cantidad'], input[name$='precio_unitario']").forEach(function (input) {
        input.addEventListener("input", calcularSubtotal);
    });

    function calcularSubtotal() {
        document.querySelectorAll(".inline-related").forEach(function (row) {
            const cantidad = row.querySelector("input[name$='cantidad']").value || 0;
            const precioUnitario = row.querySelector("input[name$='precio_unitario']").value || 0;
            const subtotalField = row.querySelector("input[name$='subtotal']");
            subtotalField.value = (parseFloat(cantidad) * parseFloat(precioUnitario)).toFixed(2);
        });
    }
});
