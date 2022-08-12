""" hooks """
import os
import falcon

def validate_access(req, _resp, _resource, _params):
    """ validate access method """
    access_key = os.environ.get('ACCESS_KEY')
    for key, value in req.params.items():
        if key == 'ACCESS_KEY':
            ACCESS_KEY = value
    if not access_key or ACCESS_KEY != access_key:
        raise falcon.HTTPForbidden(description='Access Denied')
