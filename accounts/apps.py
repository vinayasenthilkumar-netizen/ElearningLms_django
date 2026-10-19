# import the base django class
from django.apps import AppConfig


# create the config class for the accounts app
class AccountsConfig(AppConfig):

    name = 'accounts'
    def ready(self):

        # import signals 
        import accounts.signals