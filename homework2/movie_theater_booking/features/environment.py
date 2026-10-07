"""Run Behave against a disposable Django test database, never the demo data."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_theater_booking.settings")
import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.test.runner import DiscoverRunner
from rest_framework.test import APIClient


def before_all(context):
    context.runner = DiscoverRunner(verbosity=0, interactive=False)
    context.runner.setup_test_environment()
    context.database_config = context.runner.setup_databases()


def before_scenario(context, scenario):
    call_command("flush", verbosity=0, interactive=False)
    context.user = get_user_model().objects.create_user("bdd-viewer", password="bdd-sample-pass-2026")
    context.other = get_user_model().objects.create_user("bdd-other", password="bdd-sample-pass-2026")
    context.api = APIClient()
    context.web = Client()


def after_all(context):
    context.runner.teardown_databases(context.database_config)
    context.runner.teardown_test_environment()
