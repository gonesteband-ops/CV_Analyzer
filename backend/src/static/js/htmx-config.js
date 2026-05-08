/**
 * Configuración de HTMX para AI-Recruiter Pro.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Configurar headers por defecto para CSRF
  htmx.config.defaultHeaders = {
    'X-Requested-With': 'XMLHttpRequest'
  };

  // Configurar timeout
  htmx.config.timeout = 30000; // 30 segundos

  // Configurar indicador de carga
  htmx.config.showOnCallbacks = true;

  // Mostrar indicador de carga en requests (excepto formularios e inputs)
  document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const elt = evt.detail.elt;
    // NO deshabilitar: FORM, BUTTON, INPUT, TEXTAREA, SELECT
    const nonDisableable = ['FORM', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT'];
    if (!nonDisableable.includes(elt.tagName)) {
      elt.classList.add('opacity-75', 'cursor-not-allowed');
      if (elt.disabled !== undefined) {
        elt.disabled = true;
      }
    }
  });

  document.body.addEventListener('htmx:afterRequest', function(evt) {
    const elt = evt.detail.elt;
    const nonDisableable = ['FORM', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT'];
    if (!nonDisableable.includes(elt.tagName)) {
      elt.classList.remove('opacity-75', 'cursor-not-allowed');
      if (elt.disabled !== undefined) {
        elt.disabled = false;
      }
    }
  });

  // Manejar errores de manera global
  document.body.addEventListener('htmx:responseError', function(evt) {
    console.error('HTMX Error:', evt.detail);

    // Mostrar notificación de error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-danger-500 text-white px-6 py-4 rounded-lg shadow-lg z-50';
    errorDiv.innerHTML = `
      <p class="font-semibold">Error</p>
      <p class="text-sm">No se pudo completar la solicitud. Intente nuevamente.</p>
    `;

    document.body.appendChild(errorDiv);

    // Remover después de 5 segundos
    setTimeout(() => {
      errorDiv.remove();
    }, 5000);
  });

  // Configurar confirmación para operaciones destructivas
  document.body.addEventListener('htmx:confirm', function(evt) {
    const elt = evt.detail.elt;

    // Verificar si el elemento tiene la clase 'confirm-delete'
    if (elt.classList.contains('confirm-delete')) {
      const confirmed = confirm('¿Está seguro que desea eliminar este elemento? Esta acción no se puede deshacer.');
      if (!confirmed) {
        evt.preventDefault();
        return false;
      }
    }
  });

  // Configurar swap por defecto
  htmx.config.defaultSwapStyle = 'innerHTML';
  htmx.config.defaultSwapDelay = 0;
  htmx.config.settleDelay = 20;
});
