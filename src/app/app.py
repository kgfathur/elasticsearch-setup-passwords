import os
import sys
import requests
import urllib3
import json
import time
import logging
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser
from distutils.util import strtobool

from ezconfig import EZConfig

log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
log.addHandler(handler)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def set_passwd():
    log.debug("SETPASS_RESET = {}".format(configs['set_password']))
    log.debug("SETPASS_MASTER = {}".format(configs['set_master']))

    passwords = {}
    set_password = strtobool(configs['set_password'])
    set_master = strtobool(configs['set_master'])
    master_password = configs['master_password']
    
    if (set_password == True):
        if (set_master == True):
            log.debug('Set using master password')
            if (master_password != None and master_password != ''):
                if (len(master_password) < 6):
                    log.error('Passwords must be at least [6] characters long')
                    log.info('Operation aborted')
                    sys.exit(0)
                else:
                    for user in users:
                        passwords[user] = master_password
            else:
                log.error('Master password not set!')
                log.info('Operation aborted')
                sys.exit(0)
        else:
            log.debug('Set using individual password')            
            for user in users:
                passwords[user] = configs[user]

    # response = requests.get(url, auth = HTTPBasicAuth('elastic', 'ChangeMe'), verify='/ca.crt')

        responCode = 404
        elastic_username = configs['elastic_username']
        elastic_password = configs['elastic_password']
        elastic_url = configs['elastic_url']
        
        max_retries = configs['max_retries']
        retry_interval = configs['retry_interval']

        if max_retries != None:
            try:
                max_retries = int(max_retries)
            except Exception as e:
                log.error('Exception: {}'.format(e))
                
                log.error('\nGet SETPASS_RETRIES [{}], positive integer expected'.format(max_retries))
                sys.exit(0)

            if (max_retries < 1):
                sys.exit(0)
        
        if retry_interval != None:
            try:
                retry_interval = int(retry_interval)
            except Exception as e:
                log.error('Exception: {}'.format(e))
                
                log.error('\nGet retry interval [{}], positive integer expected'.format(retry_interval))
                sys.exit(0)

            if (retry_interval < 1):
                retry_interval = 3
                log.warning('\nGet retry interval [{}], set to minimum [{}]'.format(retry_interval, retry_interval))
        cluster_status = "red"
        response = None
        while ((responCode == 404) or (cluster_status == 'red') or (cluster_status == 'yellow')) and (max_retries > 0):
            endpoint = '/_cluster/health'
            url = '{}{}'.format(elastic_url, endpoint)
            print('Trying to authenticate: {} with user [{}]'.format(url, elastic_username))
            try:
                response = requests.get(url, auth = HTTPBasicAuth(elastic_username, elastic_password), verify=False)
                responCode = response.status_code

            except Exception as e:
                log.error('Exception: {}'.format(e))
                log.debug('- - - - - - - - - - - - - - - -')
                log.info('Retrying in {} second(s)'.format(retry_interval))
                max_retries -= 1
                log.info('Attempt to retry: {} left'.format(max_retries))
                log.debug('- - - - - - - - - - - - - - - -')
                time.sleep(retry_interval)
            else:
                if (responCode == 200):
                    log.info('Authentication SUCCESS')
                    cluster_response = json.loads(response.content)
                    cluster_status = cluster_response['status']
                    print(json.dumps(cluster_response, indent=2))
                    break
                elif (responCode == 401):
                    log.error('Authentication Failure: {} for user [{}]'.format(url, elastic_username))
        
        if (responCode == 200):
            responCode = 404
            while (responCode == 404) and max_retries > 0:
                endpoint = '/_security/user'
                url = '{}{}'.format(elastic_url, endpoint)
                log.info('Trying to authenticate: {} with user [{}]'.format(url, elastic_username))
                try:
                    response = requests.get(url, auth = HTTPBasicAuth(elastic_username, elastic_password), verify=False)
                    responCode = response.status_code

                except Exception as e:
                    log.error('Exception: {}'.format(e))
                    log.debug('- - - - - - - - - - - - - - - -')
                    log.info('Retrying in {} second(s)'.format(retry_interval))
                    max_retries -= 1
                    log.info('Attempt to retry: {} left'.format(max_retries))
                    log.debug('- - - - - - - - - - - - - - - -')
                    time.sleep(retry_interval)
                else:
                    if (responCode == 200):
                        log.info('Authentication SUCCESS')
                        break
                    elif (responCode == 401):
                        log.error('Authentication Failure: {} for user [{}]'.format(url, elastic_username))
        changed = {}
        change_count = 0
        if (responCode == 200):
            json_response = json.loads(response.content)
            
            for username in json_response.keys():
                if username in passwords.keys():
                    headers = {'Content-type': 'application/json'}
                    endpoint = '/_security/user/{}/_password'.format(username)
                    url = '{}{}'.format(elastic_url, endpoint)
                    user_data = {}
                    try:
                        user_data['password'] = passwords[username]
                        data_json = json.dumps(user_data)
                        try:
                            log.info('Trying user password change call {}'.format(url))
                            response = requests.post(url, headers = headers, data = data_json, auth = HTTPBasicAuth(elastic_username, elastic_password), verify=False)
                            responCode = response.status_code
                            log.debug('Response ({}): {}'.format(responCode, json.dumps(json.loads(response.content), indent=2)))
                            if (responCode == 200):        
                                log.info('Changed password for user [{}]'.format(username))
                                changed[username] = 'True'
                                change_count += 1
                                if (username == elastic_username):
                                    elastic_password = passwords[username]
                            else:
                                changed[username] = 'False'
                        except Exception as e:
                            changed[username] = 'False'
                            log.error('Exception: {}'.format(e))
                    except Exception as e:
                        changed[username] = 'False'
                        log.error('username [{}] not in list'.format(username))
                        log.error('Exception: {}'.format(e))
                else:
                    changed[username] = 'False'
                    log.error('User [{}] not in list'.format(username))
            print()
            log.info('- - - - - - - - - - - - - - - - - - - - - - -')
            log.info("        Changed Password Summary")
            log.info("          {} user(s) affected".format(change_count))
            print()
            for user, change in changed.items():
                print("  - {:<25} {}".format(user, change))
            log.info('- - - - - - - - - - - - - - - - - - - - - - -')
            print()
                            
        elif (responCode == 401):
            json_response = json.loads(response.content)
            print(json.dumps(json_response, indent=2))
            if 'error' in json_response.keys():
                log.error(json_response['error']['reason'])
    else:
        print('Operation aborted')

def main():
    global ec
    global using_config
    global configs
    global users
    config_params = ['max_retries',
                    'retry_interval',
                    'elastic_url', 
                    'elastic_username',
                    'elastic_password',
                    'set_password',
                    'set_master',
                    'master_password',
                    'elastic',
                    'apm_system',
                    'kibana',
                    'kibana_system',
                    'logstash_system',
                    'beats_system',
                    'remote_monitoring_user'
                    ]
    users = ['elastic',
            'apm_system',
            'kibana',
            'kibana_system',
            'logstash_system',
            'beats_system',
            'remote_monitoring_user'
            ]
    workdir = os.path.dirname(os.path.abspath(__file__))
    log.debug('workdir: {}'.format(workdir))
    
    config_file = os.getenv('CONFIG_FILE')
    if config_file == None:
        config_file = '{}/config.conf'.format(workdir)
        log.warning("CONFIG_FILE not set")
        log.info("Using default config file:")
        log.info("  '{}'".format(config_file))
    else:
        log.info('config_file: {}'.format(config_file))
    
    default_config = ConfigParser()
    default_config.read_string("""
    [ES_CONFIG]
    elastic_url = https://elasticsearch:9200
    elastic_username = elastic
    max_retries = 5
    retry_interval = 3
    set_password = False
    set_master = True
    """)
    
    using_config = True
    if config_file == None:
        using_config = False
        log.warning("Configuration file not set")
        log.warning("It recommended to set password using Configuration file")
        log.info("Set environtment variable with CONFIG_FILE=PATH")
        log.info("PATH to the Configuration can use secrets")
        log.info("Continue using environtment variable...")
    else:
        using_config = True
        if not os.path.isfile(config_file):
            log.error("Config file:")
            log.error("  '{}' Not Exist".format(config_file))
            log.info("Continue using environtment variable...")
            config_file = 'default param'
            using_config = False
            ec = EZConfig(default_config = default_config)
        else:
            ec = EZConfig(config_file = config_file, default_config = default_config)

    configs = {}
    use_env = 0
    use_cfg = 0
    for param in config_params:
        value = os.getenv(param)
        if (value == None) or (value == ''):
            value = ec.get('ES_CONFIG', param)
            log.debug("Get '[{}]' from config file [{}]".format(param, config_file))
            use_cfg += 1
        else:
            log.debug("Get '[{}]' from environtment variable".format(param))
            use_env += 1

        if value == None:
            log.warning('{} = None'.format(param))
        configs[param] = value
    if use_env > 0:
        log.info("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
        log.warning("Some configuration parameter using environtment variable")
        log.warning("Please remove container after password(s) set")
        log.info("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    if use_cfg > 0:
        log.info("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
        log.warning("Some configuration parameter using config file")
        log.warning("Please keep your config file secure")
        log.warning("or delete the config file after password(s) set")
        log.info("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    
    set_passwd()

if __name__ == "__main__":
    main()