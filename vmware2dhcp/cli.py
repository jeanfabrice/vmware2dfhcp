#!/usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2019 Jean-Fabrice
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import argparse
import logging
import os
import sys
from vmware2dhcp import Vmware2dhcp
import yaml
import pkg_resources

# default values
DEFAULT_DHCP_ADDRESS = 'localhost'
DEFAULT_DHCP_GROUP = ''
DEFAULT_DHCP_KEY_NAME = 'omapi_key'
DEFAULT_DHCP_KEY_VALUE = 'REVGQVVMVF9ESENQX0tFWV9WQUxVRQ=='
DEFAULT_DHCP_PORT = 7991
DEFAULT_PROM_ENABLED = True
DEFAULT_PROM_PORT = 8000
DEFAULT_VC_ADDRESS = 'localhost'
DEFAULT_VC_CUSTOMATTRIBUTE_DHCPOPTION_NAMESPACE = 'dhcp.'
DEFAULT_VC_PASSWORD = 'password'
DEFAULT_VC_USERNAME = 'admin'
DEFAULT_VM_NETWORKS = []

# List of supported log level stanza for this app
_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'VERSION'), 'r') as fh:
  __version__ = fh.readline().strip()

def _log_level_string_to_int(log_level_string):
  # source: https://www.fun4jimmy.com/2015/09/15/configuring-pythons-logging-module-with-argparse.html
  if not log_level_string in _LOG_LEVEL_STRINGS:
    message = 'invalid choice: {0} (choose from {1})'.format(log_level_string, _LOG_LEVEL_STRINGS)
    raise argparse.ArgumentTypeError(message)

  log_level_int = getattr(logging, log_level_string, logging.INFO)
  # check the logging log_level_choices have not changed from our expected values
  assert isinstance(log_level_int, int)

  return log_level_int

def parseArgs():
  global args
  parser = argparse.ArgumentParser(description='Populate isc-dhcp-server with VMs living in a VMware environment')
  parser.add_argument('-c', '--config', dest='configfile', help='Config file')
  parser.add_argument('-l', '--log-level', default='INFO', type=_log_level_string_to_int, dest='log_level', help='Set the logging output level: {0}'.format(_LOG_LEVEL_STRINGS))
  parser.add_argument('--version', action='version', version=__version__)
  args = parser.parse_args()

def loadConfiguration():
  configfiledata = {}
  if args.configfile:
    try:
      with open(args.configfile, 'r') as stream:
        try:
          configfiledata = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
          sys.exit('Can\'t read YAML config file: {0}'.format(e))
    except Exception as e:
      sys.exit('Can\'t open config file: {0}'.format(e))

  cfg={
    'dhcp_address': os.environ['V2D_DHCP_ADDRESS'] if 'V2D_DHCP_ADDRESS' in os.environ else (configfiledata['dhcp_address'] if 'dhcp_address' in configfiledata else DEFAULT_DHCP_ADDRESS ),
    'dhcp_group': os.environ['V2D_DHCP_GROUP'] if 'V2D_DHCP_GROUP' in os.environ else (configfiledata['dhcp_group'] if 'dhcp_group' in configfiledata else DEFAULT_DHCP_GROUP ),
    'dhcp_key_name': os.environ['V2D_DHCP_KEY_NAME'] if 'V2D_DHCP_KEY_NAME' in os.environ else (configfiledata['dhcp_key_name'] if 'dhcp_key_name' in configfiledata else DEFAULT_DHCP_KEY_NAME ),
    'dhcp_key_value': os.environ['V2D_DHCP_KEY_VALUE'] if 'V2D_DHCP_KEY_VALUE' in os.environ else (configfiledata['dhcp_key_value'] if 'dhcp_key_value' in configfiledata else DEFAULT_DHCP_KEY_VALUE ),
    'dhcp_port': os.environ['V2D_DHCP_PORT'] if 'V2D_DHCP_PORT' in os.environ else (configfiledata['dhcp_port'] if 'dhcp_port' in configfiledata else DEFAULT_DHCP_PORT ),
    'prom_enabled': os.environ['V2D_PROM_ENABLED'] if 'V2D_PROM_ENABLED' in os.environ else (configfiledata['prom_enabled'] if 'prom_enabled' in configfiledata else DEFAULT_PROM_ENABLED ),
    'prom_port': os.environ['V2D_PROM_PORT'] if 'V2D_PROM_PORT' in os.environ else (configfiledata['prom_port'] if 'prom_port' in configfiledata else DEFAULT_PROM_PORT ),
    'vc_address': os.environ['V2D_VC_ADDRESS'] if 'V2D_VC_ADDRESS' in os.environ else (configfiledata['vc_address'] if 'vc_address' in configfiledata else DEFAULT_VC_ADDRESS ),
    'vc_customattribute_dhcpoption_namespace': os.environ['V2D_VC_CUSTOMATTRIBUTE_DHCPOPTION_NAMESPACE'] if 'V2D_VC_CUSTOMATTRIBUTE_DHCPOPTION_NAMESPACE' in os.environ else (configfiledata['vc_customattribute_dhcpoption_namespace'] if 'vc_customattribute_dhcpoption_namespace' in configfiledata else DEFAULT_VC_CUSTOMATTRIBUTE_DHCPOPTION_NAMESPACE ),
    'vc_password': os.environ['V2D_VC_PASSWORD'] if 'V2D_VC_PASSWORD' in os.environ else (configfiledata['vc_password'] if 'vc_password' in configfiledata else DEFAULT_VC_PASSWORD ),
    'vc_username': os.environ['V2D_VC_USERNAME'] if 'V2D_VC_USERNAME' in os.environ else (configfiledata['vc_username'] if 'vc_username' in configfiledata else DEFAULT_VC_USERNAME ),
    'vm_networks': os.environ['V2D_VM_NETWORKS'].split(',') if 'V2D_VM_NETWORKS' in os.environ else (configfiledata['vm_networks'] if 'vm_networks' in configfiledata else DEFAULT_VM_NETWORKS ),
  }
  return cfg

def setLoglevel():
  logging.basicConfig(level=args.log_level,format='[%(name)s] %(asctime)s %(filename)s %(funcName)s(%(lineno)d): %(message)s')

def run():
  parseArgs()
  setLoglevel()
  cfg = loadConfiguration()
  v = Vmware2dhcp(cfg)
  v.start()

if __name__ == '__main__':
  run()
