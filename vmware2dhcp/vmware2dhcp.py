#!/usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2019 Jean-Fabrice BOBO
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import atexit
import logging
import os
import pypureomapi
import re
import ssl
import struct
import sys
import time
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim # See https://github.com/vmware/pyvmomi pylint: disable=no-name-in-module
from datetime import datetime, timedelta
from pytz import timezone
from prometheus_client import start_http_server, Counter, Gauge, Summary, Info

# time (in seconds) between Vmware event checks
SLEEP_TIME = 5

# See https://pubs.vmware.com/vsphere-6-5/topic/com.vmware.wssdk.apiref.doc/vim.event.VmEvent.html
VMWARE_MONITORED_ADD_EVENTS = [vim.event.VmCreatedEvent]
VMWARE_MONITORED_UPDATE_EVENTS = [vim.event.VmReconfiguredEvent, vim.event.VmMacChangedEvent, vim.event.VmRenamedEvent, vim.event.VmStartingEvent, vim.event.VmPoweredOnEvent]
VMWARE_MONITORED_REMOVE_EVENTS = [vim.event.VmRemovedEvent]
VMWARE_MONITORED_EVENTS = VMWARE_MONITORED_ADD_EVENTS + VMWARE_MONITORED_UPDATE_EVENTS + VMWARE_MONITORED_REMOVE_EVENTS
VMWARE_EVENTS_PAGE_SIZE = 1000

# See https://pubs.vmware.com/vsphere-6-5/topic/com.vmware.vspsdk.apiref.doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html
UNMANAGED_GUESTID_REGEXP = r'^win.+'

# Sample validating and catching regexp for virtual machine FQDN based name
FQDN_VALIDATION_REGEXP = re.compile('^([a-zA-Z0-9][a-zA-Z0-9-]*)[.]([a-zA-Z0-9-.]+)')

FILTER_EVENT_COUNT   = Counter('vmware2dhcp_filtering_event_total', 'VM filtering events', ['vc', 'dhcp', 'event'])
FILTER_EVENT_LATENCY = Summary('vmware2dhcp_filtering_events_latency_seconds', 'VM filtering latency', ['vc', 'dhcp', 'filter'])
DHCPD_LATENCY        = Summary('vmware2dhcp_dhcpd_latency_seconds', 'dhcpd server latency', ['vc', 'dhcp', 'stage'])
VSPHERE_LATENCY      = Summary('vmware2dhcp_vsphere_latency_seconds', 'VSphere server latency', ['vc', 'dhcp', 'stage'])
VMWARE_EVENT_COUNT   = Counter('vmware2dhcp_vmware_event_total', 'VM events received', ['vc', 'dhcp', 'event'])
FAILURE_COUNT        = Counter('vmware2dhcp_exception', 'Vmware2dhcp exceptions raised', ['vc', 'dhcp', 'exception'])

logger = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'VERSION'), 'r') as fh:
  __version__ = fh.readline().strip()


class MyOmapi(pypureomapi.Omapi):
  def __init__(self, hostname, port, username=None, key=None, timeout=None):
    super(MyOmapi, self).__init__(hostname, port, username.encode('utf8'), key.encode('utf8'), timeout)

  def add_host_with_options(self, mac, options={}, group=None):
    optionList=[]
    msg = pypureomapi.OmapiMessage.open(b'host')
    msg.message.append((b'create', struct.pack('!I', 1)))
    msg.message.append((b'exclusive', struct.pack('!I', 1)))
    msg.obj.append((b'hardware-type', struct.pack('!I', 1)))
    msg.obj.append((b'hardware-address', pypureomapi.pack_mac(mac)))

    for key, value in options.items():
      optionList.append('option {0} "{1}";'.format(key,value))
    if optionList:
      msg.obj.append((b'statements', ''.join(optionList).lower().encode('utf8')))

    # unsupported since group takes precedence over options
    # if group:
    #   msg.obj.append((b'group', group.encode('utf8')))

    logger.debug('Omapi message: {0}'.format(msg.obj))

    response = self.query_server(msg)
    if response.opcode !=  pypureomapi.OMAPI_OP_UPDATE:
      raise pypureomapi.OmapiError('Add failed')


class Vmware2dhcp():
  def __init__(self, cfg):
    self.cfg=cfg


  def createTimeFilter(self,vStartTime, vEndTime):
      localTimeFilter = vim.event.EventFilterSpec.ByTime()
      localTimeFilter.beginTime = vStartTime
      localTimeFilter.endTime = vEndTime
      return localTimeFilter

  def filterEvent(self,event):

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_vm').time():
      # Filter out event if we don't have any associated VM
      if event.vm is None:
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='no_vm').inc()
        return False

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_vmconfig').time():
      # Filter out event if we don't have access to the VM hardware configuration
      if event.vm.vm.config is None:
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='no_vmconfig').inc()
        return False

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_network').time():
      # Filter out event if the VM doesn't live on a provisioning subnet
      if self.cfg['vm_networks']:
        inMonitoredVmNetwork = False
        for network in event.vm.vm.network:
          if network.name in self.cfg['vm_networks']:
            inMonitoredVmNetwork = True
            break
        if not inMonitoredVmNetwork:
          FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='bad_network').inc()
          return False

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_device').time():
      # Filter out event if the VM doesn't have any attached device
      if event.vm.vm.config.hardware.device is None:
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='no_device').inc()
        return

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_network_interface').time():
      # Filter out event if the VM doesn't have any network interface
      hasEthernetCard = False
      for dev in event.vm.vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard):
          hasEthernetCard = True
          break
      if not hasEthernetCard:
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='no_network_interface').inc()
        return False

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_os').time():
      # Filter out if the registered guest OS is not managed by our DHCP
      if re.match(UNMANAGED_GUESTID_REGEXP, event.vm.vm.config.guestId, re.IGNORECASE):
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='unsupported_os').inc()
        return False

    with FILTER_EVENT_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], filter='check_name').time():
      # Filter out badly formatted VM name
      if not FQDN_VALIDATION_REGEXP.match(event.vm.vm.config.name):
        FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='bad_name').inc()
        return False

    # we have a winner!
    FILTER_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event='accepted').inc()
    return True

  def dhcpConnect(self):
    global dhcpServer
    logger.info('Connecting to DHCP server: {0}'.format(self.cfg['dhcp_address']))
    try:
      dhcpServer = MyOmapi(self.cfg['dhcp_address'], self.cfg['dhcp_port'], self.cfg['dhcp_key_name'], self.cfg['dhcp_key_value'])
    except Exception as e:
      logger.critical('Unable to connect to DHCP server: {0}'.format(e))
      sys.exit(-1)
    logger.info('Connected to DHCP server!')

  def dhcpDisconnect(self):
    global dhcpServer
    logger.info('Disconnecting from DHCP server: {0}'.format(self.cfg['dhcp_address']))
    try:
      dhcpServer.close()
    except Exception as e:
      logger.critical('Error occured during disconnection: {0}'.format(e))
    logger.info('Disconnected from DHCP server')


  def registerVm(self,vm,cf):
    global dhcpServer
    macAddressList = []
    relevantCustomFields = {}
    dhcpOptions = {}

    logger.debug('List of published custom attributes: {0}'.format(cf))

    with DHCPD_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='connect').time():
      self.dhcpConnect()

    for field in cf:
      if field.managedObjectType == vim.VirtualMachine and field.name.startswith(self.cfg['vc_customattribute_dhcpoption_namespace']):
        relevantCustomFields[field.key] = re.sub('^%s' % re.escape(self.cfg['vc_customattribute_dhcpoption_namespace']), '', field.name)

    logger.debug('List of custom attributes that will be pushed as dhcp option: {0}'.format(relevantCustomFields))

    # Split name/domain-name from VM name
    fqdnMatch = FQDN_VALIDATION_REGEXP.match(vm.config.name)

    # Looking for the VM mac addresses
    for dev in vm.config.hardware.device:
      if isinstance(dev, vim.vm.device.VirtualEthernetCard):
        macAddressList.append(dev.macAddress)

    for field in vm.customValue:
      if field.key in relevantCustomFields:
        dhcpOptions[relevantCustomFields[field.key]]= field.value

    for macAddress in macAddressList:
      while True:

        try:
          with DHCPD_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='del_host').time():
            dhcpServer.del_host(macAddress)
        except pypureomapi.OmapiErrorNotFound as e:
          FAILURE_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], exception=e).inc()
          pass
        except Exception as e:
          FAILURE_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], exception=e).inc()
          logger.error('Error occured while unregistring VM in DHCP server: {0}'.format(e))

        try:
          dhcpOptions['host-name'] = fqdnMatch.group(1)
          dhcpOptions['domain-name'] = fqdnMatch.group(2)
          logger.debug('DHCP options: {0}'.format(dhcpOptions))
          logger.debug('Mac address: {0}'.format(macAddress))
          with DHCPD_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='add_host').time():
            dhcpServer.add_host_with_options(macAddress, dhcpOptions, self.cfg['dhcp_group'] )
        except Exception as e:
          FAILURE_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], exception=e).inc()
          logger.error('Error occured while registring VM in DHCP server: {0}'.format(e))

        break

    with DHCPD_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='disconnect').time():
      self.dhcpDisconnect()

    return

  def start(self):
    # Disable SSL certificate checking
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE

    # Start Prometheus client if asked to
    if self.cfg['prom_enabled']:
      start_http_server( self.cfg['prom_port'] )

    # set Info metric
    i = Info('vmware2dhcp_info', 'A metric with a constant \'1\' value labeled by several service info')
    i.info({'version': __version__, 'vc': self.cfg['vc_address'], 'dhcp': self.cfg['dhcp_address']})

    si = None
    # Getting the Service Instance
    logger.info('Connecting to VSphere server: {0}'.format(self.cfg['vc_address']))
    try:
      with VSPHERE_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='connect').time():
        si = SmartConnect(protocol='https',host=self.cfg['vc_address'],port=443,user=self.cfg['vc_username'],pwd=self.cfg['vc_password'],sslContext=context)
    except Exception as e:
      print('Could not connect to the specified vCenter, please check the provided address, username and password: {0}'.format(e))
      raise SystemExit(-1)
    logger.info('Connected to VSphere server!')

    #Cleanly disconnect
    atexit.register(Disconnect, si)
    em = si.content.eventManager
    efs = vim.event.EventFilterSpec(eventTypeId=list(map(lambda x: x.__name__,VMWARE_MONITORED_EVENTS)))
    now = datetime.now(timezone('UTC'))
    efs.time = self.createTimeFilter(now,now)
    ehc = em.CreateCollectorForEvents(efs)
    ehc.SetCollectorPageSize(VMWARE_EVENTS_PAGE_SIZE)
    lastEventTimeUTC = None

    while True:
      if lastEventTimeUTC is not None:
        logger.info('Waiting for event. Last event time: {0}'.format(lastEventTimeUTC))
        startTime = lastEventTimeUTC + timedelta(seconds=1)
        endTime = datetime.now(timezone('UTC'))
        efs.time = self.createTimeFilter(startTime,endTime)
        try:
          ehc.DestroyCollector()
          ehc = em.CreateCollectorForEvents(efs)
        except:
          lastEventTimeUTC = lastEventTimeUTC + timedelta(seconds=1)
      else:
        lastEventTimeUTC = now
      with VSPHERE_LATENCY.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], stage='read_next_events').time():
        events = ehc.ReadNextEvents(VMWARE_EVENTS_PAGE_SIZE)

      while len(events) > 0:
        logger.debug('Received {0} event(s)'.format(len(events)))
        for idx, event in enumerate(events):
          logger.debug('Event #{0} at {1}: {2}'.format(idx, event.createdTime, event.fullFormattedMessage))
          logger.debug('Event data: {0}'.format(event))

          VMWARE_EVENT_COUNT.labels(vc=self.cfg['vc_address'], dhcp=self.cfg['dhcp_address'], event=event.__class__.__name__).inc()

          if isinstance(event, tuple(VMWARE_MONITORED_ADD_EVENTS)):
            if self.filterEvent(event):
              self.registerVm(event.vm.vm, si.content.customFieldsManager.field)
          elif isinstance(event, tuple(VMWARE_MONITORED_UPDATE_EVENTS)):
            if self.filterEvent(event):
              self.registerVm(event.vm.vm, si.content.customFieldsManager.field)
          elif isinstance(event, tuple(VMWARE_MONITORED_REMOVE_EVENTS)):
            # not implemented. Virtual Machine object properties are lost when this event pops up
            pass
          lastEventTimeUTC = event.createdTime
        events = ehc.ReadNextEvents(VMWARE_EVENTS_PAGE_SIZE)

      time.sleep(SLEEP_TIME)
    return 0
