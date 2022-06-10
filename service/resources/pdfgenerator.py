"""Welcome export module"""
import os
import json
import traceback
import logging
import requests
import falcon
from . import utils
from .hooks import validate_access

@falcon.before(validate_access)
class PDFGenerator():
    """PDFGenerator class"""
    # pylint: disable=no-self-use
    def on_post(self, req, resp):
        """ Implement POST """
        # pylint: disable=broad-except,no-member
        output_pdf = ''
        try:
            data = json.loads(req.bounded_stream.read())
            template_file = req.get_header('TEMPLATE_FILE')
            if template_file and data:
                basename = os.path.dirname(__file__)
                output_pdf = utils.write_fillable_pdf(basename, data, template_file)
                with open(output_pdf, 'rb') as output_fd:
                    pdf = output_fd.read()
                    resp.text = pdf
                    output_fd.close()
        except Exception as error:
            print(f"Failed to generate PDF: {error}")
            print(traceback.format_exc())
            resp.status = falcon.HTTP_500   # pylint: disable=no-member
            resp.text = json.dumps(str(error))
        finally: # clean up
            if len(output_pdf) > 1:
                os.remove(output_pdf)
    # pylint: disable=no-self-use, too-many-locals
    def send_email(self, request, emails, file_url, email_type):
        """
        send emails applicant and staff
        """
        template = {
            "url": request["staff_email_template"],
            "replacements": {
                "data": request
            }
        }
        subject = request['data']["ContractorApplicantName"] + " applied for a solar permit at " + request['data']["projectAddress"]
        email_to = emails["staffs"]
        #applicant email
        if email_type == "applicants":
            subject = "You applied for a solar permit at " + request['data']["projectAddress"]
            email_to = emails["applicants"]
            template = {
                "url": request["applicant_email_template"],
                "replacements": {
                    "data": request
                }
            }

        file_name = request['data']["projectAddress"] + "-app.pdf"
        payload = {
            "subject": subject,
            "attachments": [
                {
                    "content": "",
                    "path": file_url,
                    "filename": file_name,
                    "type": "application/pdf"
                }
            ],
            "to": email_to,
            "from": emails["from"],
            "template": template
        }
        headers = {
            'x-apikey': os.environ.get('X_APIKEY'),
            'Content-Type': 'application/json',
            'Accept': 'text/plain'
        }
        result = None
        json_data = json.dumps(payload)
        try:
            result = requests.post(
                os.environ.get('EMAIL_SERVICE_URL'),
                headers=headers,
                data=json_data)
        except requests.exceptions.HTTPError as errh:
            logging.exception("HTTPError: %s", errh)
        except requests.exceptions.ConnectionError as errc:
            logging.exception("Error Connecting: %s", errc)
        except requests.exceptions.Timeout as errt:
            logging.exception("Timeout Error: %s", errt)
        except requests.exceptions.RequestException as err:
            logging.exception("OOps: Something Else: %s", err)

        return result
