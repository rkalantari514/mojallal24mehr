from django.apps import AppConfig

class MahakupdateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mahakupdate'

    def ready(self):
        import mahakupdate.signals  # فایل سیگنال‌ها را import کنید
