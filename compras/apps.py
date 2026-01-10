from django.apps import AppConfig


class ComprasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compras'
    
    def ready(self):
        """Importar signals cuando la app esté lista."""
        import compras.signals  # noqa
