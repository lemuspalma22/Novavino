// admin_vpg_form.js
// Maneja el comportamiento del checkbox VPG en el formulario de factura

(function($) {
    $(document).ready(function() {
        var esVpgCheckbox = $('#id_es_vpg');
        var folioInput = $('#id_folio_factura');
        
        if (esVpgCheckbox.length && folioInput.length) {
            
            // Función para actualizar el estado del campo folio
            function actualizarEstadoFolio() {
                if (esVpgCheckbox.is(':checked')) {
                    folioInput.prop('readonly', true);
                    folioInput.prop('required', false);
                    folioInput.css('background-color', '#f0f0f0');
                    folioInput.val('');
                    
                    // Remover el asterisco de campo obligatorio
                    folioInput.closest('.form-row').removeClass('required');
                    
                    // Agregar mensaje informativo si no existe
                    if ($('#vpg-info-message').length === 0) {
                        folioInput.after(
                            '<p id="vpg-info-message" style="color: #27ae60; font-weight: bold; margin-top: 5px;">' +
                            '✓ El folio VPG se generará automáticamente al guardar (formato: VPG26-X)' +
                            '</p>'
                        );
                    }
                } else {
                    folioInput.prop('readonly', false);
                    folioInput.prop('required', true);
                    folioInput.css('background-color', '');
                    folioInput.closest('.form-row').addClass('required');
                    $('#vpg-info-message').remove();
                }
            }
            
            // Ejecutar al cargar la página
            actualizarEstadoFolio();
            
            // Ejecutar cuando cambie el checkbox
            esVpgCheckbox.on('change', actualizarEstadoFolio);
        }
    });
})(django.jQuery);
