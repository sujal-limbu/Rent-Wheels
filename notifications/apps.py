from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        """Start the background scheduler when Django starts."""
        import os
        # Only start in the main process, not in Django's reloader child process
        if os.environ.get('RUN_MAIN') != 'true':
            from . import scheduler
            scheduler.start()