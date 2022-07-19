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
    api_key = ''

    def on_post(self, req, resp):
        """ Implement POST """
        # pylint: disable=broad-except,no-member
        try:
            data =  self.retrieve_submissions()
            if data:
                basename = os.path.dirname(__file__)
                for request in data:
                    output_file = utils.write_fillable_pdf(basename, request['data'])
                    result = self.send_email(request['data'], output_file)
                    submission_id = request['_id']
                    if result == 200:
                        self.delete_submission(PDFGenerator.api_key, submission_id)
        except Exception as error:
            print(f"Failed to generate PDF: {error}")
            print(traceback.format_exc())
            resp.status = falcon.HTTP_500   # pylint: disable=no-member
            resp.text = json.dumps(str(error))

    def retrieve_submissions(self):
        """ retrieve submissions"""
        email = os.environ.get('EMAIL')
        password = os.environ.get('PASSWORD')
        login_url = 'https://formio.form.io/user/login/submission?live=1'

        payload = json.dumps({
                "data": {
                   "email":email,
                    "password": password
                }
            })
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", login_url, headers=headers, data=payload)
            jwt_token = response.headers['x-jwt-token']
            url = "https://jotielkyhqtrqtb.form.io/newpatientregistration/submission?limit=10"
            payload={}
            headers = {
                'x-jwt-token': jwt_token
            }
            PDFGenerator.api_key = jwt_token
            response = requests.request("GET", url, headers=headers, data=payload)
            return response.json()
        except Exception as err: # pylint: disable=broad-except
            print("login error: {0}".format(err))
            return None

    def delete_submission(self, api_key, submission_id):
        """helper function for deleting a submission on formio"""

        delete_url = 'https://jotielkyhqtrqtb.form.io/newpatientregistration/submission/' + str(submission_id)
        payload = {}
        files = {}
        headers = {
            'x-jwt-token': api_key
        }
        print(submission_id)
        try:
            response = requests.request("DELETE", delete_url, headers=headers, \
                data=payload, files=files)
            response.raise_for_status()
            return response
        except Exception as err: # pylint: disable=broad-except
            print("deletion error: {0}".format(err))
            return None

    # pylint: disable=no-self-use, too-many-locals
    def send_email(self, request, output_pdf):
        """
        send emails
        """
        subject = "New patient registration for " + request['patientName']
        email_to = []
        email_to.append({
            "email": 'ansondentalstudio@gmail.com',
            "name": 'Anson Dental'
        })

        html_content  = "<html><body><table>"
        for key, value in request.items():
            html_content = html_content + "<tr><td>" + key + "</td><td>" + str(value) + "</td></tr>"
        html_content = html_content + "</table></body></html>"
        file_name = "new_patient.pdf"
        payload = {
            "subject": subject,
            "attachments": [
                {
                    "content": "",
                    "path": os.environ.get('BASE_URL') + "/static/" + output_pdf,
                    "filename": file_name,
                    "type": "application/pdf"
                }
            ],
            "to": email_to,
            "from": {"email": "ansondentalstudio@gmail.com", "name":  "Anson Dental Studio"},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                },
                {
                    "type": "text/custom",
                    "value": "New Patient submission"
                }
            ]
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

        return result.status_code
