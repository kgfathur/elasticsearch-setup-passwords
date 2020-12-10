import os
import sys
import requests
import urllib3
import json
import time
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

set_max_retries = os.getenv('SETPASS_RETRIES')
es_url = os.getenv('ELASTIC_URL')
es_username = os.getenv('ELASTIC_USERNAME')
es_password = os.getenv('ELASTIC_PASSWORD')

set_passwd = os.getenv('SETPASS_RESET')
set_master = os.getenv('SETPASS_MASTER')
set_master_password = os.getenv('SETPASS_master_password')

print("SETPASS_RESET = {}".format(set_passwd))
print("SETPASS_MASTER = {}".format(set_master))

max_retries = 0
if set_max_retries != None:
    try:
        max_retries = int(set_max_retries)
    except Exception as e:
        print('Exception: {}'.format(e))
        
        print('\nGet SETPASS_RETRIES [{}], positive integer expected'.format(set_max_retries))
        sys.exit(0)

    if (max_retries < 1):
        sys.exit(0)
else:
    print('Set MAX RETRIES to default [10]')
    max_retries = 10

passwords = {}

if (set_passwd == True or set_passwd == 'True' or set_passwd == 'true' or set_passwd == 'TRUE'):
    if (set_master == True or set_master == 'True' or set_master == 'true' or set_master == 'TRUE'):
        print('Set using master password')
        if (set_master_password != None and set_master_password != ''):
            if (len(set_master_password) < 6):
                print('Passwords must be at least [6] characters long')
                print('Operation aborted')
                sys.exit(0)
            else:
                passwords['elastic'] = set_master_password
                passwords['apm_system'] = set_master_password
                passwords['kibana'] = set_master_password
                passwords['kibana_system'] = set_master_password
                passwords['logstash_system'] = set_master_password
                passwords['beats_system'] = set_master_password
                passwords['remote_monitoring_user'] = set_master_password
        else:
            print('But, master password not set!')
            print('Operation aborted')
            sys.exit(0)
    else:
        print('Set using individual password')
        passwords['elastic'] = os.getenv('SETPASS_elastic')
        passwords['apm_system'] = os.getenv('SETPASS_apm_system')
        passwords['kibana'] = os.getenv('SETPASS_kibana')
        passwords['kibana_system'] = os.getenv('SETPASS_kibana_system')
        passwords['logstash_system'] = os.getenv('SETPASS_logstash_system')
        passwords['beats_system'] = os.getenv('SETPASS_beats_system')
        passwords['remote_monitoring_user'] = os.getenv('SETPASS_remote_monitoring_user')

# response = requests.get(url, auth = HTTPBasicAuth('elastic', 'Admin123'), verify='/home/thur/git/espy/ca.crt')

    responCode = 404
    while (responCode == 404) and max_retries > 0:
        endpoint = '/_security/user'
        url = '{}{}'.format(es_url, endpoint)
        print('Trying to authenticate: {} with user [{}]'.format(url, es_username))
        try:
            response = requests.get(url, auth = HTTPBasicAuth(es_username, es_password), verify=False)
            responCode = response.status_code

        except Exception as e:
            print('Exception: {}'.format(e))
            time.sleep(3)
            max_retries -= 1
            print('- - - - - - - - - - - - - - - -')
            print('Attempt to retry: {}'.format(max_retries))
            print('- - - - - - - - - - - - - - - -')
        else:
            if (responCode == 200):
                print('Authentication SUCCESS')
            elif (responCode == 401):
                print('Authentication Failure for user [{}]'.format(es_username))

    if (responCode == 200):
        json_response = json.loads(response.content)
        print(json.dumps(json_response, indent=2))
        user_count = 0
        for username in json_response.keys():
            if username in passwords.keys():
                headers = {'Content-type': 'application/json'}
                endpoint = '/_security/user/{}/_password'.format(username)
                url = '{}{}'.format(es_url, endpoint)
                user_data = {}

                user_data['password'] = passwords[username]
                data_json = json.dumps(user_data)
                try:
                    print('\nTrying user password change call {}'.format(url))
                    response = requests.post(url, headers = headers, data = data_json, auth = HTTPBasicAuth(es_username, es_password), verify=False)
                    responCode = response.status_code
                    print('Response ({}):\n{}'.format(responCode, json.dumps(json.loads(response.content), indent=2)))
                    if (responCode == 200):        
                        print('Changed password for user [{}]'.format(username))
                        if (username == es_username):
                            es_password = passwords[username]
                except Exception as e:
                    print('Exception: {}'.format(e))
            else:
                print('User [{}] not in list'.format(username))
                
    elif (responCode == 401):
        json_response = json.loads(response.content)
        print(json.dumps(json_response, indent=2))
        if 'error' in json_response.keys():
            print(json_response['error']['reason'])
else:
    print('Operation aborted')