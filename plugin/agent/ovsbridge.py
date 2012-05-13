#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2011 Nicira Networks, Inc.
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
# @author: Somik Behera, Nicira Networks, Inc.
# @author: Brad Hall, Nicira Networks, Inc.
# @author: Dan Wendlandt, Nicira Networks, Inc.
# @author: Dave Lapsley, Nicira Networks, Inc.

from vifport import VifPort

class OVSBridge:
    def __init__(self, br_name, root_helper):
        self.br_name = br_name
        self.root_helper = root_helper

    def run_cmd(self, args):
        cmd = shlex.split(self.root_helper) + args
        LOG.debug("## running command: " + " ".join(cmd))
        p = Popen(cmd, stdout=PIPE)
        retval = p.communicate()[0]
        if p.returncode == -(signal.SIGALRM):
            LOG.debug("## timeout running command: " + " ".join(cmd))
        return retval

    def run_vsctl(self, args):
        full_args = ["ovs-vsctl", "--timeout=2"] + args
        return self.run_cmd(full_args)

    def reset_bridge(self):
        self.run_vsctl(["--", "--if-exists", "del-br", self.br_name])
        self.run_vsctl(["add-br", self.br_name])

    def delete_port(self, port_name):
        self.run_vsctl(["--", "--if-exists", "del-port", self.br_name,
          port_name])

    def set_db_attribute(self, table_name, record, column, value):
        args = ["set", table_name, record, "%s=%s" % (column, value)]
        self.run_vsctl(args)

    def clear_db_attribute(self, table_name, record, column):
        args = ["clear", table_name, record, column]
        self.run_vsctl(args)

    def run_ofctl(self, cmd, args):
        full_args = ["ovs-ofctl", cmd, self.br_name] + args
        return self.run_cmd(full_args)

    def remove_all_flows(self):
        self.run_ofctl("del-flows", [])

    def get_port_ofport(self, port_name):
        return self.db_get_val("Interface", port_name, "ofport")

    def add_flow(self, **dict):
        if "actions" not in dict:
            raise Exception("must specify one or more actions")
        if "priority" not in dict:
            dict["priority"] = "0"

        flow_str = "priority=%s" % dict["priority"]
        if "match" in dict:
            flow_str += "," + dict["match"]
        flow_str += ",actions=%s" % (dict["actions"])
        self.run_ofctl("add-flow", [flow_str])

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

    def add_tunnel_port(self, port_name, remote_ip):
        self.run_vsctl(["add-port", self.br_name, port_name])
        self.set_db_attribute("Interface", port_name, "type", "gre")
        self.set_db_attribute("Interface", port_name, "options", "remote_ip=" +
            remote_ip)
        self.set_db_attribute("Interface", port_name, "options", "in_key=flow")
        self.set_db_attribute("Interface", port_name, "options",
            "out_key=flow")
        return self.get_port_ofport(port_name)

    def add_patch_port(self, local_name, remote_name):
        self.run_vsctl(["add-port", self.br_name, local_name])
        self.set_db_attribute("Interface", local_name, "type", "patch")
        self.set_db_attribute("Interface", local_name, "options", "peer=" +
                              remote_name)
        return self.get_port_ofport(local_name)

    def db_get_map(self, table, record, column):
        str = self.run_vsctl(["get", table, record, column]).rstrip("\n\r")
        return self.db_str_to_map(str)

    def db_get_val(self, table, record, column):
        return self.run_vsctl(["get", table, record, column]).rstrip("\n\r")

    def db_str_to_map(self, full_str):
        list = full_str.strip("{}").split(", ")
        ret = {}
        for e in list:
            if e.find("=") == -1:
                continue
            arr = e.split("=")
            ret[arr[0]] = arr[1].strip("\"")
        return ret

    def get_port_name_list(self):
        res = self.run_vsctl(["list-ports", self.br_name])
        return res.split("\n")[0:-1]

    def get_port_stats(self, port_name):
        return self.db_get_map("Interface", port_name, "statistics")

    def get_xapi_iface_id(self, xs_vif_uuid):
        return self.run_cmd(
                        ["xe",
                        "vif-param-get",
                        "param-name=other-config",
                        "param-key=nicira-iface-id",
                        "uuid=%s" % xs_vif_uuid]).strip()

    # returns a VIF object for each VIF port
    def get_vif_ports(self):
        edge_ports = []
        port_names = self.get_port_name_list()
        for name in port_names:
            external_ids = self.db_get_map("Interface", name, "external_ids")
            ofport = self.db_get_val("Interface", name, "ofport")
            if "iface-id" in external_ids and "attached-mac" in external_ids:
                p = VifPort(name, ofport, external_ids["iface-id"],
                            external_ids["attached-mac"], self)
                edge_ports.append(p)
            elif "xs-vif-uuid" in external_ids and \
                 "attached-mac" in external_ids:
                # if this is a xenserver and iface-id is not automatically
                # synced to OVS from XAPI, we grab it from XAPI directly
                iface_id = self.get_xapi_iface_id(external_ids["xs-vif-uuid"])
                p = VifPort(name, ofport, iface_id,
                            external_ids["attached-mac"], self)
                edge_ports.append(p)

        return edge_ports
