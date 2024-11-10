#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# cython: language_level=3
    
"""This module is to publish a dataset into Zenodo and obtain the DOI
"""

import os
import sys
import requests
import json
from urllib.parse import urljoin
import requests
import io
import zipfile

# https://developers.zenodo.org/
# https://zenodo.org/signup/

CLIENT_ID = "74lt6WgB5ljmsXTutMtXmQ3BIZfDQYtqEarAmDV1"
CLIENT_SECRET = "SAv98mNow8dDklGJa4mbR5eIOZJDDbAIddIj0RzAUS6XrZJpls8cACKcZr9n"

"""
Authorize URL (GET)
https://zenodo.org/oauth/authorize
Query parameters (example request):

response_type (required, use code or token)
client_id (required)
scope (required, space separate list of scopes)
redirect_uri (required, URL encoded)
state (recommended, for CSRF protection)

Access token URL (POST)
https://zenodo.org/oauth/token
Request body parameters:

client_id (required).
client_secret (required).
grant_type (required, use client_credentials, refresh_token, authorization_code).
code (required for grant_type authorization code).
scope (required for grant_type client_credentials).
refresh_token (required for grant_type refresh_token).
"""

ZENODO_PROD = "https://zenodo.org"
ZENODO_SANDBOX = "https://sandbox.zenodo.org"

APP_KEYS = {
    'prod': {
        'server': ZENODO_PROD,
        'client_id': '74lt6WgB5ljmsXTutMtXmQ3BIZfDQYtqEarAmDV1',
        'client_secret': 'SAv98mNow8dDklGJa4mbR5eIOZJDDbAIddIj0RzAUS6XrZJpls8cACKcZr9n',
    },
    'sandbox': {
        'server': ZENODO_SANDBOX,
        'client_id': '8N5iaqC8rZJd1U3LVnpdUdZ0eVB7ku4aHuX2x9eB',
        'client_secret': 'ajqPxI20rFgzBtucZZYbcwWhqd6cAE1VVc9Sntpv1KTq3RPipz7FqY0S6ev5',
    },
}


def get_token(environment: str, scope: str):
    """_summary_

    Args:
        environment (str): Environment selection. Valid values are 'prod' and 'sandbox'
        scope (str): Scope for the token. E.g. 'deposit:write'

    Returns:
        dict: Dictionary with the token. Example: 
            {
                'access_token': 'L36Cn6AZYRqkSwuhcyKeh2Otu9h1tr', 
                'expires_in': 5184000, 
                'token_type': 'Bearer', 
                'scope': 'deposit:write',
                'user': {'id': '24229'}
            }
        
    """
    
    di_token: dict = None
    keys = APP_KEYS[environment]
    url =  urljoin(keys['server'], '/oauth/token')
    data = {
        'client_id': keys['client_id'],
        'client_secret': keys['client_secret'],
        'grant_type': 'client_credentials',
        'scope': scope
        #'scope': 'deposit:write'
    }
    
    r = requests.post(url, data=data, timeout = 10)
    
    status_code = r.status_code
    if status_code >= 200 and status_code< 300:
        di_token = r.json()
    elif status_code >= 300 and status_code< 400:
        print(f"Redirection {status_code}")
    elif status_code >= 400 and status_code< 500:
         print(f"Client error {status_code}: {r.text}")
    elif status_code >= 500 and status_code< 600:
        print(f"Server error {status_code}: {r.text}")
    else:
        print(f"Status code {status_code}")

    
    
    try:
        print(r.status_code)
        print(r.json())
    except:
        pass
    
    return di_token

def get_depositions(environment, access_token):
    d = None
    keys = APP_KEYS[environment]
    url =  urljoin(keys['server'], '/api/deposit/depositions')
    headers = {"Content-Type": "application/json"}
    params = {'access_token': access_token}
    
    """
    Headers are not necessary here since "requests" automatically
    adds "Content-Type: application/json", because we're using
    the "json=" keyword argument
    headers=headers, 
    """
    
    r = requests.post(url,
                    params=params,
                    json={},
                    headers=headers,
                    timeout = 10)
    
    status_code = r.status_code
    if status_code >= 200 and status_code< 300:
        d = r.json()
    elif status_code >= 300 and status_code< 400:
        print(f"Redirection {status_code}")
    elif status_code >= 400 and status_code< 500:
         print(f"Client error {status_code}: {r.text}")
    elif status_code >= 500 and status_code< 600:
        print(f"Server error {status_code}: {r.text}")
    else:
        print(f"Status code {status_code}")
    return d

def upload_file(ENV, access_token, depositions, fn):
    file_result = None
    bucket_url = depositions["links"]["bucket"]
    params = {'access_token': access_token}
    
    # Verify that the data file exists
    if os.path.isfile(fn) is False:
        raise FileNotFoundError(fn)
    
    # https://proxiesapi.com/articles/uploading-zip-files-via-http-post-with-python-requests
    # Create in-memory zip file
    
    # We wrap the zip file in an io.BytesIO stream so Requests can read it but we don't have to save it locally
    with io.BytesIO() as data:
        # Create the zip file and move cursor to beginning
        with zipfile.ZipFile(data, mode="w") as z:
            z.write(fn)
        data.seek(0)
        
        # Put the file in the bucket
        filename = os.path.basename(fn)
        r = requests.put(
            "%s/%s" % (bucket_url, filename),
            data=data,
            params=params,
            timeout = 10
        )
        status_code = r.status_code
        if status_code >= 200 and status_code< 300:
            file_result = r.json()
        elif status_code >= 300 and status_code< 400:
            print(f"Redirection {status_code}")
        elif status_code >= 400 and status_code< 500:
            print(f"Client error {status_code}: {r.text}")
        elif status_code >= 500 and status_code< 600:
            print(f"Server error {status_code}: {r.text}")
        else:
            print(f"Status code {status_code}")
    
    return file_result

if __name__ == "__main__":
    ENV = 'sandbox'
    di_token = get_token(ENV, scope='deposit:write')
    if di_token is not None:
        access_token = di_token['access_token']
        depositions = get_depositions(ENV, access_token)
        if depositions is not None:
            fn = os.path.join('dataset','top100_2024films.csv')
            file_result = upload_file(ENV, access_token, depositions, fn)
            
