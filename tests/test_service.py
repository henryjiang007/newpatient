# pylint: disable=redefined-outer-name
"""Tests for microservice"""
import os
import json
from unittest.mock import patch
from falcon import testing
import pytest
import requests
import jsend
import service.microservice
from service.resources import utils

CLIENT_HEADERS = {
    "ACCESS_KEY": "123456"
}
CLIENT_ENV = {
    "ACCESS_KEY": CLIENT_HEADERS["ACCESS_KEY"]
}

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service(), headers=CLIENT_HEADERS)

@pytest.fixture
def mock_env_access_key(monkeypatch):
    """ mock environment access key """
    for key in CLIENT_ENV:
        monkeypatch.setenv(key, CLIENT_ENV[key])

@pytest.fixture
def mock_env_no_access_key(monkeypatch):
    """ mock environment with no access key """
    monkeypatch.delenv("ACCESS_KEY", raising=False)

def test_welcome(client, mock_env_access_key):
    # pylint: disable=unused-argument
    # mock_env_access_key is a fixture and creates a false positive for pylint
    """Test welcome message response"""
    response = client.simulate_get('/welcome')
    assert response.status_code == 200

    expected_msg = jsend.success({'message': 'Welcome'})
    assert json.loads(response.content) == expected_msg

    # Test welcome request with no ACCESS_KEY in header
    client_no_access_key = testing.TestClient(service.microservice.start_service())
    response = client_no_access_key.simulate_get('/welcome')
    assert response.status_code == 403

def test_welcome_no_access_key(client, mock_env_no_access_key):
    # pylint: disable=unused-argument
    # mock_env_no_access_key is a fixture and creates a false positive for pylint
    """Test welcome request with no ACCESS_key environment var set"""
    response = client.simulate_get('/welcome')
    assert response.status_code == 403

def test_pdfgenerator_post(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """
        Test pdf generator
    """
    with open('tests/mocks/submissions.json', 'r') as file_obj:
        mock_data = json.load(file_obj)
    assert mock_data

    # happy path
    response = client.simulate_post(
        '/generate-pdf',
        json=mock_data,
        headers={"TEMPLATE_FILE": "https://sfdsoewd.blob.core.usgovcloudapi.net/uploads/solarpanel/SolarPanelTemplatev3.pdf"}
    )
    assert response.status_code == 200
    assert len(response.content) > 1000

    # exceptions: ValueError
    response = client.simulate_post(
        '/generate-pdf',
        json={"dummy": "data"},
        headers={"TEMPLATE_FILE": "https://sfdsoewd.blob.core.usgovcloudapi.net/uploads/solarpanel/SolarPanelTemplate3.pdf"}
    )
    assert response.status_code == 500


def test_formfields_get(client):
    # pylint: disable=unused-argument
    """
        Test form field definition
    """
    with open('tests/mocks/formfielddef.json', 'r') as file_obj:
        mock_formfielddef = json.load(file_obj)
    assert mock_formfielddef

    # happy path
    response = client.simulate_get(
        '/get-formfield-definition',
        headers={"TEMPLATE_FILE": "https://sfdsoewd.blob.core.usgovcloudapi.net/uploads/solarpanel/SolarPanelTemplatev3.pdf"}
    )
    assert response.status_code == 200

    # exceptions
    response = client.simulate_get(
        '/get-formfield-definition',
        headers={"_FILE": "https://fakeurl.com/SolarPanelTemplatev3.pdf"}
    )

    assert response.status_code == 500
