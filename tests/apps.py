from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'
    verbose_name = 'Imtihonlar'
<<<<<<< HEAD

    def ready(self):
        """Ensure admin registrations are imported; log any import errors.
        This helps when autodiscover is skipped or a silent error hides models.
        """
        try:
            import tests.admin  # noqa: F401
        except Exception as e:
            # Best-effort: print to console so it appears in server logs
            try:
                import traceback
                print("[tests.apps.TestsConfig] Failed to import tests.admin:\n", traceback.format_exc())
            except Exception:
                print(f"[tests.apps.TestsConfig] Failed to import tests.admin: {e}")

        # Fallback: ensure critical models are registered in admin
        try:
            from django.contrib import admin
            from . import models as _m
            to_register = [
                (_m.Exam, None),
                (_m.ExamAccess, None),
                (_m.ExamAttempt, None),
            ]
            for model, admin_cls in to_register:
                if model not in admin.site._registry:
                    try:
                        admin.site.register(model, admin_cls or admin.ModelAdmin)
                    except Exception:
                        # Don't break app startup on registration issues
                        pass
        except Exception:
            pass
=======
>>>>>>> 009973f (fix)
