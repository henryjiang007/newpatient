"""Main application module"""
import os
import json
import jsend
import sentry_sdk
import falcon
from .resources.welcome import Welcome
from .resources.pdfgenerator import PDFGenerator
from .resources.formfields import FormFieldDef

def start_service():
    """Start this service
    set SENTRY_DSN environmental variable to enable logging with Sentry
    """
    # Initialize Sentry
    sentry_sdk.init(os.environ.get('SENTRY_DSN'))
    # Initialize Falcon
    api = falcon.App()
    api.add_route('/welcome', Welcome())
    api.add_route('/generate-pdf', PDFGenerator())
    api.add_route('/get-formfield-definition', FormFieldDef())
    return api

