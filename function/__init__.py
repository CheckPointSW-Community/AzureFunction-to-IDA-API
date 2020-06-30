import os
import json
import azure.functions as func
import requests
import logging
import pathlib
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    req_body = req.get_json()
    report = []
    gw_list = open(pathlib.Path(__file__).parent / "gateways.txt", "r")
    for gw in gw_list.readlines():
        req_body = req.get_json()
        # parse host and shared secret from string     
        ia_api_hostip = gw.split(':')[0]
        ia_api_secret = gw.split(':')[1].strip()
        if req_body['action'].lower() == 'add':
            if 'session-timeout' in req_body and req_body['session-timeout'] >= 300: #if session-timeout does not exist or less than 300 then default to 300 seconds
                session_timeout = req_body['session-timeout']
            else:
                session_timeout = 300
            payload = {
              "shared-secret": ia_api_secret,
              "ip-address": req_body['ip'],
              "machine": "allowed host",
              "roles": [req_body['role']],
              "session-timeout": session_timeout,
              "fetch-machine-groups": 0,
              "calculate-roles": 0,
              "identity-source": "AWS SNS"
            }
            url = f'https://{ia_api_hostip}/_IA_API/v1.0/add-identity'
            post_result = send_to_gw(url, payload)
            report.append({"gateway": ia_api_hostip, "result": post_result, "session-timeout": session_timeout})
           
        elif req_body['action'].lower() == 'delete':
            payload = {
              "shared-secret": ia_api_secret,
              "ip-address": req_body['ip']
            }
            url = f'https://{ia_api_hostip}/_IA_API/v1.0/delete-identity'
            post_result = send_to_gw(url, payload)
            report.append({"gateway": ia_api_hostip, "result": post_result})
    gw_list.close()
    return func.HttpResponse(f"{report}") #returning an HttpResponse because the list object is not allowed to be returned 
def send_to_gw(url, payload):
    print(f'URL: {url}')
    print(f'Payload: {payload}')
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5, verify=False)
        resp.raise_for_status()
        if resp.status_code == 200:
            respcontent = json.loads(resp.content)
            return f'SUCCESS<{resp.status_code}>,{respcontent}'
        else:
            return f'ERROR<{resp.status_code}>'
    except Timeout as timeout_err:
        print(f'Timeout error occurred: {timeout_err}')
        return 'ERROR<TIMEOUT>'
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return f'ERROR<{resp.status_code}>'
    except Exception as err:
        print(f'Other error occurred: {err}')
        return 'UNEXPECTED ERROR'