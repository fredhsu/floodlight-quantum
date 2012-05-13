#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2012 Fred Hsu
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
# @author:  Fred Hsu

from ovs_quantum_agent import VifPort, OVSBridge, LocalVLANMapping, OVSQuantumAgent

from client import FLClient

# TODO: Need to import JSON libraries for adding/removing flows NO this will be done on the client

class FloodlightOVSBridge(OVSBridge):
# Need to override add and del flow using OF, and possibly init to grab the 
# controller config and add a controller component

    def __init__(self, br_name, root_helper):
        self.br_name = br_name
        self.root_helper = root_helper
        # adding dpid as global for OF
        self.datapath_id = None


# Adding set controller function from ryu
    def set_controller(self, target):
        methods = ("ssl", "tcp", "unix", "pssl", "ptcp", "punix")
        args = target.split(":")
        if not args[0] in methods:
            target = "tcp:" + target
        self.run_vsctl(["set-controller", self.br_name, target])

# Adding dpid function from ryu
    def find_datapath_id(self):
        # ovs-vsctl get Bridge br-int datapath_id
        res = self.run_vsctl(["get", "Bridge", self.br_name, "datapath_id"])

        # remove preceding/trailing double quotes
        dp_id = res.strip().strip('"')
        self.datapath_id = dp_id

    def add_flow(self, vlan_id, in_port, uplink):
        self.api.create_flows(self.datapath_id, vlan_id, in_port, uplink)


    def delete_flows(self, **dict):
        all_args = []
        if "priority" in dict:
            all_args.append("priority=%s" % dict["priority"])
        if "match" in dict:
            all_args.append(dict["match"])
        if "actions" in dict:
            all_args.append("actions=%s" % (dict["actions"]))
        flow_str = ",".join(all_args)
        self.run_ofctl("del-flows", [flow_str])

# Can probably inherit from OVSQuantumAgent
class OVSFloodlightQuantumAgent(object):

    def __init__(self, integ_br, root_helper):
        self.root_helper = root_helper
        #self.setup_integration_br(integ_br)

        # add controller stuff

        (ofp_controller_addr, ofp_rest_api_addr) = check_ofp_mode(db)

        #self.nw_id_external = rest_nw_id.NW_ID_EXTERNAL
        # TODO
        #self.api = OFPClient(ofp_rest_api_addr)
        # TODO May need to split out the ip from controller addr: "tcp:<ip>"
        # What format is controller addr in?
        self.api = FlClient(ofp_controller_addr)
        self.setup_integration_br(integ_br, ofp_controller_addr)


    def port_bound(self, port, vlan_id):
        self.int_br.set_db_attribute("Port", port.port_name, "tag",
                str(vlan_id))
        self.int_br.delete_flows(match="in_port=%s" % port.ofport)

    def port_unbound(self, port, still_exists):
        if still_exists:
            self.int_br.clear_db_attribute("Port", port.port_name, "tag")

    def setup_integration_br(self, integ_br):
        self.int_br = OVSBridge(integ_br, self.root_helper)
        self.int_br.remove_all_flows()
        # switch all traffic using L2 learning
        # TODO: Should this get replaced?  would need to add
        # existing flows from db, then could make this a 
        # lower priority flow decision
        # self.int_br.add_flow(priority=1, actions="normal")
        # TODO: from ryu these should probably go before add_flow or remove_flow
        self.int_br = OVSBridge(integ_br, self.root_helper)
        self.int_br.find_datapath_id()
        self.int_br.set_controller(ofp_controller_addr)
        # ** Floodlight will already be setup as learning switch
        # Go through each external port on the int_br and update it
        # do I need to do the above?
        #for uplink in self.int_br.get_external_ports():
        #    self._port_update(self.nw_id_external, uplink)

    # TODO Not sure if still need port update or 
    # if this can be replaced, probably
    # need some flavor of it to update all the
    # old flows during switch init
    def _port_update(self, network_id, uplink, db):
        vlan_id = db.get_vlan(network_id)
        # create a flow for each uplink port from the source port
        self.int_br.add_flow(vlan_id, in_port, uplink)

    # TODO : Need to setup loop to grab db entries and populate flows in the switch
    def daemon_loop(self, db):
        self.local_vlan_map = {}
        old_local_bindings = {}
        old_vif_ports = {}

        while True:

            all_bindings = {}
            try:
                ports = db.ports.all()
            except:
                ports = []
            for port in ports:
                all_bindings[port.interface_id] = port

            vlan_bindings = {}
            try:
                vlan_binds = db.vlan_bindings.all()
            except:
                vlan_binds = []
            for bind in vlan_binds:
                vlan_bindings[bind.network_id] = bind.vlan_id

            new_vif_ports = {}
            new_local_bindings = {}
            vif_ports = self.int_br.get_vif_ports()
            for p in vif_ports:
                new_vif_ports[p.vif_id] = p
                if p.vif_id in all_bindings:
                    net_id = all_bindings[p.vif_id].network_id
                    # Add flows for each port using the uplinks
                    for uplink in self.int_br.get_external_ports():
                        vlan_id = db.get_vlan(net_id)
                        self.int_br.add_flow(vlan_id, p, uplink)
                    new_local_bindings[p.vif_id] = net_id
                    if p not in old_vif_ports:
                        # this is a new vif port, create a flow for it
                        for uplink in self.int_br.get_external_ports():
                            self.api.create_flows(self.datapath_id, vlan_bindings[net_id], p, uplink)
                #else:
                    # no binding, put him on the 'dead vlan'
                    #self.int_br.set_db_attribute("Port", p.port_name, "tag",
                    #                             DEAD_VLAN_TAG)
                    #self.int_br.add_flow(priority=2,
                    #       match="in_port=%s" % p.ofport, actions="drop")

                old_b = old_local_bindings.get(p.vif_id, None)
                new_b = new_local_bindings.get(p.vif_id, None)

                if old_b != new_b:
                    if old_b is not None:
                        LOG.info("Removing binding to net-id = %s for %s"
                          % (old_b, str(p)))
                        self.port_unbound(p, True)
                        if p.vif_id in all_bindings:
                            all_bindings[p.vif_id].op_status = OP_STATUS_DOWN
                    if new_b is not None:
                        # If we don't have a binding we have to stick it on
                        # the dead vlan
                        net_id = all_bindings[p.vif_id].network_id
                        vlan_id = vlan_bindings.get(net_id, DEAD_VLAN_TAG)
                        self.port_bound(p, vlan_id)
                        if p.vif_id in all_bindings:
                            all_bindings[p.vif_id].op_status = OP_STATUS_UP
                        LOG.info("Adding binding to net-id = %s " \
                             "for %s on vlan %s" % (new_b, str(p), vlan_id))

            for vif_id in old_vif_ports:
                if vif_id not in new_vif_ports:
                    LOG.info("Port Disappeared: %s" % vif_id)
                    if vif_id in old_local_bindings:
                        old_b = old_local_bindings[vif_id]
                        self.port_unbound(old_vif_ports[vif_id], False)
                    if vif_id in all_bindings:
                        all_bindings[vif_id].op_status = OP_STATUS_DOWN

            old_vif_ports = new_vif_ports
            old_local_bindings = new_local_bindings
            db.commit()
            time.sleep(REFRESH_INTERVAL)

def main():
    usagestr = "%prog [OPTIONS] <config file>"
    parser = OptionParser(usage=usagestr)
    parser.add_option("-v", "--verbose", dest="verbose",
      action="store_true", default=False, help="turn on verbose logging")

    options, args = parser.parse_args()

    if options.verbose:
        LOG.basicConfig(level=LOG.DEBUG)
    else:
        LOG.basicConfig(level=LOG.WARN)

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    config_file = args[0]
    config = ConfigParser.ConfigParser()
    try:
        config.read(config_file)
    except Exception, e:
        LOG.error("Unable to parse config file \"%s\": %s"
                  % (config_file, str(e)))
        raise e


    # Get common parameters.
    try:
        integ_br = config.get("OVS", "integration-bridge")
        if not len(integ_br):
            raise Exception('Empty integration-bridge in configuration file.')

        db_connection_url = config.get("DATABASE", "sql_connection")
        if not len(db_connection_url):
            raise Exception('Empty db_connection_url in configuration file.')

        root_helper = config.get("AGENT", "root_helper")

    except Exception, e:
        LOG.error("Error parsing common params in config_file: '%s': %s"
                  % (config_file, str(e)))
        sys.exit(1)

        plugin = OVSFloodlightQuantumAgent(integ_br, root_helper)

    # Start everything.
    options = {"sql_connection": db_connection_url}
    db = SqlSoup(options["sql_connection"])
    LOG.info("Connecting to database \"%s\" on %s" %
             (db.engine.url.database, db.engine.url.host))

    plugin.daemon_loop(db)

    sys.exit(0)

if __name__ == "__main__":
    main()
