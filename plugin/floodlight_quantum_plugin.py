# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2011 Fred Hsu
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
# @author: Fred Hsu

from ovs_quantum_plugin import VlanMap
from ovs_quantum_plugin import OVSQuantumPlugin

CONF_FILE = find_config_file(
  {"plugin": "floodlight"},
  None, "floodlight_quantum_plugin.ini")

LOG.basicConfig(level=LOG.WARN)
LOG.getLogger("floodlight_quantum_plugin")

# Just use everything from the OVSQuantumPlugin
class FloodlightQuantumPlugin(OVSQuantumPlugin):
    def __init__(self, configFile=None):
        super.__init__(configFile)
