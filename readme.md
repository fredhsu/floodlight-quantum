# Introduction
This project aims to create a plugin for OpenStack Quantum using Floodlight.  The current implementation idea is to create VLANs on Open vSwitch, using Floodlight as an OpenFlow controller.  When a new machine is added, two flows will be created for ingress/egress traffic.  The flows are created using a JSON push.  

# Components
There are two components, the module that is inserted into Floodlight, and the plugin that goes into Quantum.  The module seems to be working (see example below), but the plugin still needs some work and is not functional at this point.

# Example
Here is an example curl to create some flows using the provided module:
    curl -d '{"switch": "00:00:00:00:00:00:00:01", "vlan" : "2", "ingress-port" : "1", "uplink" : "2", "entryName" : "test"}' http://localhost:8080/wm/quantum/json


