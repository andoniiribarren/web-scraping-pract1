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
import zlib

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


def get_token(env: str, scope: str) -> dict:
    """_summary_

    Args:
        env (str): Environment selection. Valid values are 'prod' and 'sandbox'
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
    keys = APP_KEYS[env]
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

def get_depositions(env:str, access_token:str, deposition_id:int=None) -> dict:
    """_summary_

    Args:
        ENV (str): environment selection to retrieve the dictionary with server url and client keys
        access_token (str): token to use the API
        deposition_id (int, optional): Deposition identifier. Defaults to None.

    Returns:
        dict: Depositions received from Zenodo
    """
    d = None
    keys = APP_KEYS[env]
    
    url =  urljoin(keys['server'], '/api/deposit/depositions')
    if deposition_id is not None:
        # URL to retrieve deposition
        url =  f'{url}/{str(deposition_id)}'
    
    headers = {"Content-Type": "application/json"}
    params = {'access_token': access_token}
    
    if deposition_id is None:
        # Create deposition
        r = requests.post(url,
                        params=params,
                        json={},
                        headers=headers,
                        timeout = 10)
    else:
        # Retrieve deposition
        r = requests.get(url,
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


def upload_file(access_token:str, depositions:object, fn:str) -> dict:
    """Upload file to deposition in zenodo

    Args:
        access_token (str): token to use the API
        depositions (object): depositions retrieved from Zenodo
        fn (str): filename of the file to upload

    Raises:
        FileNotFoundError: _description_

    Returns:
        dict: result received from Zenodo
    """
    file_result = None
    bucket_url = depositions["links"]["bucket"]
    params = {'access_token': access_token}
    # headers = {
    #     'Content-Encoding': 'gzip'
    # }
    
    # Verify that the data file exists
    if os.path.isfile(fn) is False:
        raise FileNotFoundError(fn)
    
    # https://proxiesapi.com/articles/uploading-zip-files-via-http-post-with-python-requests
    # Create in-memory zip file
    
    # # We wrap the zip file in an io.BytesIO stream so Requests can read it but we don't have to save it locally
    # with io.BytesIO() as data:
    #     # Create the zip file and move cursor to beginning
    #     with zipfile.ZipFile(data, mode="w") as z:
    #         z.write(fn)
    #     data.seek(0)
    
    with open(fn, "rb") as data:
        
        # Put the file in the bucket
        filename = os.path.basename(fn)
        url = f"{bucket_url}/{filename}"
        r = requests.put(
            url,
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

def upload_metadata(env:str, access_token:str, deposition_id:int) -> dict:
    """_summary_

    Args:
        env (str): environment selection to retrieve the dictionary with server url and client keys
        access_token (str): token to use the API
        deposition_id (int): Deposition identifier.

    Returns:
        dict: result received from Zenodo
    """
    
    result = None
    keys = APP_KEYS[env]
    url =  urljoin(keys['server'], f'/api/deposit/depositions/{deposition_id}')
    params = {'access_token': access_token}
    headers = {'Content-Type': 'application/json'}

    data = {
        'metadata': {
            'title': "M2.851.PR1",
            'upload_type': 'dataset',
            'description': "Film Affinity Top Movies 2024",
            'creators': [
                {'name': "Andoni Iribarren González", 'affiliation': "Universitat Oberta de Catalunya"},
                {'name': "Juan Pedro Rodríguez", 'affiliation': "Universitat Oberta de Catalunya"}
            ]
        }
    }
    

    r = requests.put(
        url,
        data=json.dumps(data),
        params = params,
        headers = headers,
        timeout = 10
    )
    status_code = r.status_code
    if status_code >= 200 and status_code< 300:
        result = r.json()
    elif status_code >= 300 and status_code< 400:
        print(f"Redirection {status_code}")
    elif status_code >= 400 and status_code< 500:
        print(f"Client error {status_code}: {r.text}")
    elif status_code >= 500 and status_code< 600:
        print(f"Server error {status_code}: {r.text}")
    else:
        print(f"Status code {status_code}")
    

    return result


def delete_file(env:str, access_token:str, deposition_id:int, file_id:int) -> dict:
    """_summary_

    Args:
        env (str): environment selection to retrieve the dictionary with server url and client keys
        access_token (str): token to use the API
        deposition_id (int): Deposition identifier.
        file_id (int): File identifier in the deposition

    Returns:
        dict: result received from Zenodo
    """
    result = None
    keys = APP_KEYS[env]
    url =  urljoin(keys['server'], f'/api/deposit/depositions/{deposition_id}/files/{file_id}')
    params = {'access_token': access_token}
    headers = {'Content-Type': 'application/json'}
    

    r = requests.delete(
        url,
        params = params,
        headers = headers,
        timeout = 10
    )
    status_code = r.status_code
    if status_code >= 200 and status_code< 300:
        result = r.json()
    elif status_code >= 300 and status_code< 400:
        print(f"Redirection {status_code}")
    elif status_code >= 400 and status_code< 500:
        print(f"Client error {status_code}: {r.text}")
    elif status_code >= 500 and status_code< 600:
        print(f"Server error {status_code}: {r.text}")
    else:
        print(f"Status code {status_code}")
    

    return result

def deposition_action(env:str, deposition_id:int, action: str) -> dict:
    """Execute an action on a Zenodo deposition

    https://developers.zenodo.org/

    Args:
        env (str): _environment selection to retrieve the dictionary with server url and client keys
        deposition_id (int): Deposition identifier.
        action (str): Action to execute

    Returns:
        dict: result received from Zenodo
    """
    result = None
    
    # Get new token with scope deposit:actions
    di_actions_token = get_token(env, scope='deposit:actions')
    access_token = di_actions_token['access_token']
    
    keys = APP_KEYS[env]
    # https://developers.zenodo.org/#deposition-actions
    # deposit:actions
    url =  urljoin(keys['server'], f'/api/deposit/depositions/{deposition_id}/actions/{action}')
    params = {'access_token': access_token}
    headers = {'Content-Type': 'application/json'}
    
    r = requests.post(url,
                    params=params,
                    json={},
                    headers=headers,
                    timeout = 10)
    status_code = r.status_code
    if status_code >= 200 and status_code< 300:
        result = r.json()
    elif status_code >= 300 and status_code< 400:
        print(f"Redirection {status_code}")
    elif status_code >= 400 and status_code< 500:
        print(f"Client error {status_code}: {r.text}")
    elif status_code >= 500 and status_code< 600:
        print(f"Server error {status_code}: {r.text}")
    else:
        print(f"Status code {status_code}")
    
    
    return result

def publish_deposition(env:str, deposition_id:int) -> dict:
    """Publish a deposition in Zenodo

    Args:
        env (str): _environment selection to retrieve the dictionary with server url and client keys
        deposition_id (int): Deposition identifier.

    Returns:
        dict: result received from Zenodo
    """
    return deposition_action(env, deposition_id, 'publish')

def edit_deposition(env:str, deposition_id:int) -> dict:
    """Enable edition of a deposition in Zenodo

    Args:
        env (str): _environment selection to retrieve the dictionary with server url and client keys
        deposition_id (int): Deposition identifier.

    Returns:
        dict: result received from Zenodo
    """
    return deposition_action(env, deposition_id, 'edit')
    

DEPOSITION_ID = None
CSV_FN = 'top100_2024films.csv'

if __name__ == "__main__":
    ENV = 'prod'
    di_token = get_token(ENV, scope='deposit:write')
    if di_token is not None:
        access_token = di_token['access_token']
        deposition_id = DEPOSITION_ID
        depositions = get_depositions(ENV, access_token, deposition_id)
        if depositions is not None:
            deposition_id = depositions['id']
            # Upload the file
            fn = os.path.join('dataset', CSV_FN)
            file_result = upload_file(access_token, depositions, fn)
            r = upload_metadata(ENV, access_token, deposition_id)
            
    publish_result = publish_deposition(ENV, deposition_id)
    print(f"DOI URL = {publish_result['doi_url']}")
    
    # sandbox
    # 'https://doi.org/10.5072/zenodo.129385'
    
    # prod
    # DOI: '10.5281/zenodo.14077232'
    # https://doi.org/10.5281/zenodo.14077232
    
    # New DOI: 10.5281/zenodo.14078194
    # https://zenodo.org/records/14078194

    # Final run:
    # DOI: 10.5281/zenodo.14078918
    # DOI URL = https://doi.org/10.5281/zenodo.14078918
    # https://zenodo.org/badge/DOI/10.5281/zenodo.14078918.svg

    pass