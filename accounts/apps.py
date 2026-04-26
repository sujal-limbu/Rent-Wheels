from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals

        try:
            from django.contrib.sites.models import Site
            Site.objects.filter(id=1).update(
                domain='rent-wheels-i6qi.onrender.com',
                name='RentWheels'
            )
        except Exception:
            pass