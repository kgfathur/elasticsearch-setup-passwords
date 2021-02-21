import os
import glob
import json
import logging
from configparser import ConfigParser

log = logging.getLogger()

class EZConfig:
    def __init__(self, config_file = None, default_config = None, confdir = 'conf.d', workdir = None, debug = False):
        
        load_default_section = False
        loaded_config = ConfigParser()
        
        self.config = ConfigParser()
        self.confdir = confdir

        if workdir is None:
            self.workdir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.workdir = workdir

        if default_config is None:
            self.default_config = {}
            log.warning("No 'default_config' parameter given")
        else:
            self.default_config = default_config

        config_files = glob.glob('{}/{}/*.conf'.format(self.workdir, self.confdir))
        config_files.sort()

        if config_file is None:
            default_config_file = "{}/config.conf".format(self.workdir)
            config_files.insert(0, default_config_file)
            self.config_file = config_files
            if not os.path.isfile(default_config_file):
                log.error("Default config ({}) not exist! creating...".format(default_config_file))
                try:
                    with open(default_config_file, 'w') as create_config_file:
                        loaded_config = default_config
                        loaded_config.write(create_config_file)

                except Exception as ei:
                    log.error('Exception > {}'.format(ei))
        else:
            if config_file.startswith('/'):
                self.config_file = config_file
            elif config_file.startswith('~/'):
                try:
                    self.config_file = os.getenv('HOME') + config_file
                except Exception as ei:
                    log.error('Exception > {}'.format(ei))
            else:
                self.config_file = "{}/{}".format(self.workdir, config_file)
            
            if not os.path.isfile(self.config_file):
                log.error ("Configuration file ({}) not exist! Proccess aborted!".format(self.config_file))
                os.sys.exit(1)
        
        loaded_config.read(self.config_file)
        self.config = loaded_config

        for config_section in self.default_config.keys():
            
            if debug:
                log.debug(config_section)
            if not load_default_section:
                if config_section == 'DEFAULT':
                    if debug:
                        log.debug('LOAD_DEFAULT_SECTION = False')
                    continue
            for config_item in self.default_config[config_section]:
                if config_item in loaded_config[config_section]:
                    self.config[config_section][config_item] = loaded_config[config_section][config_item]
                    # if debug:
                    #     print('  - {} = {}'.format(config_item, loaded_config[config_section][config_item]))
                else:
                    self.config[config_section][config_item] = default_config[config_section][config_item]
                    if debug:
                        log.debug("No loaded_config item for '{}'".format(config_item))
                        log.debug("Set default {} = {}".format(config_item, default_config[config_section][config_item]))
                
                if debug:
                    log.debug('  - {} = {}'.format(config_item, self.config[config_section][config_item]))
    
    def get(self, section = None, item = None, debug = False):
        value = None
        if section in self.config.sections():
            if item in self.config[section]:
                value = self.config[section][item]
            else:
                value = None
        else:
            value = None
        
        return value
    
def main():
    
    workdir = os.path.dirname(os.path.abspath(__file__))
    log.debug('main workdir: {}'.format(workdir))

if __name__ == "__main__":
    main()