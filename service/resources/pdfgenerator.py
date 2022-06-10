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
            if data:
                basename = os.path.dirname(__file__)
                output_pdf = utils.write_fillable_pdf(basename, data)
                self.send_email(data['request'], output_pdf)
        except Exception as error:
            print(f"Failed to generate PDF: {error}")
            print(traceback.format_exc())
            resp.status = falcon.HTTP_500   # pylint: disable=no-member
            resp.text = json.dumps(str(error))
        finally: # clean up
            if len(output_pdf) > 1:
                os.remove(output_pdf)

    # pylint: disable=no-self-use, too-many-locals
    def send_email(self, request, output_pdf):
        """
        send emails
        """
        subject = "New patient registration for " + request['data']['patientName']
        email_to = []
        for email in request['emails']['to']:
            email_to.append({
                "email": email["email"],
                "name": email["name"]
            })

        file_name = "new_patient.pdf"
        payload = {
            "subject": subject,
            "attachments": [
                {
                    "content": "",
                    "path": output_pdf,
                    "filename": file_name,
                    "type": "application/pdf"
                }
            ],
            "to": email_to,
            "from": request['emails']['from']
        }
        headers = {
            'ACCESS_KEY': os.environ.get('MYEMAIL_ACCESS_KEY'),
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
