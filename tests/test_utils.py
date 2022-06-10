# pylint: disable=redefined-outer-name
"""Tests for microservice"""
import json
import os
from testfixtures import ShouldRaise
from service.resources import utils

BASENAME = os.path.dirname(__file__)
FILE_URL = "https://sfdsoewd.blob.core.usgovcloudapi.net/uploads/solarpanel/SolarPanelTemplatev3.pdf"
FILE_INPUT = BASENAME + "/template/SolarPanelTemplateTest.pdf"
FILE_OUTPUT = BASENAME + "/filled/test_output.pdf"

#  pylint: disable=unspecified-encoding
with open('tests/mocks/submissions.json', 'r') as file_obj:
    mock_data = json.load(file_obj)

with open('tests/mocks/bad-submission.json', 'r') as file_obj:
    bad_mock_data = json.load(file_obj)

def test_write_fillable_pdf():
    # pylint: disable=unused-argument
    """
        Test utils: write fillable pdf
    """
    # happy path
    response = utils.write_fillable_pdf(BASENAME, mock_data, FILE_URL)
    assert len(response) > len(BASENAME)

    # exceptions - IOError
    with ShouldRaise(Exception):
        fakebasename = "dummy/" + BASENAME
        utils.write_fillable_pdf(fakebasename, mock_data, FILE_URL)

    # exceptions - ValueError
    with ShouldRaise(Exception):
        bad_file_url = FILE_URL + ".pdf"
        utils.write_fillable_pdf(BASENAME, mock_data, bad_file_url)

def test_merge_pdf():
    # pylint: disable=unused-argument
    """
        Test utils: merge_pdf
    """
    # happy path
    response = utils.merge_pdf(FILE_INPUT, FILE_OUTPUT, mock_data)
    assert response == FILE_OUTPUT

    # exceptions - ValueError
    with ShouldRaise(Exception):
        bad_input = FILE_URL + ".pdf"
        response = utils.merge_pdf(bad_input, FILE_OUTPUT, mock_data)

    os.remove(FILE_OUTPUT)
