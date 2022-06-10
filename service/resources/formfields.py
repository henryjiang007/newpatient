"""PDf form def export module"""
import os
import json
import traceback

from . import utils

class FormFieldDef():
    """PDF form field def class"""
    # pylint: disable=no-self-use, too-few-public-methods
    def on_get(self, req, resp):
        """ Implement GET """
        # pylint: disable=broad-except,no-member
        template_pdf = ''
        formfield_def = ''
        try:
            template_file = req.get_header('TEMPLATE_FILE')
            if template_file:
                basename = basename = os.path.dirname(__file__)
                template_pdf = utils.get_pdf_template(basename, template_file)
                #template_pdf = os.path.join(basename, 'template/SolarPanelTemplateTest1.pdf')
                formfield_def = utils.get_pdf_keys(template_pdf)
                resp.text = json.dumps(formfield_def)
            else:
                raise Exception

        except Exception as error:
            print(f"Failed get form field definition: {error}")
            print(traceback.format_exc())
            resp.text = json.dumps(str(error))
            resp.status = 500
        finally: # done with the temp file
            resp.text = json.dumps(formfield_def)
