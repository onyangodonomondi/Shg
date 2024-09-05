from django.apps import AppConfig

class MembersConfig(AppConfig):
    name = 'members'

    def ready(self):
        import members.signals  # Import the signals here