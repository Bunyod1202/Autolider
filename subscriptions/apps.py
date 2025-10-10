from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        # Import signal handlers to keep user.is_active in sync on manual edits
        try:
            import importlib
            importlib.import_module('subscriptions.signals')
        except Exception as e:
            # Avoid crashing app on import-time issues; log instead
            print(f"subscriptions.signals import error: {e}")
