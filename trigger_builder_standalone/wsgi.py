import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trigger_builder_standalone.settings")

application = get_wsgi_application()
