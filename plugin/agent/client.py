# Copyright (C) 2012 Fred Hsu <fredlhsu at gmail dot com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# @Author Fred Hsu

import httplib
import urlparse
import json
import urllib2
# need to import json library

class FlClient(object):

    quantum_path = '/quantum/'

    def __init__(self, address):
        r = urlparse.SplitResult('', address, '', '', '')
        self.host = r.hostname
        self.port = r.port
        #self.url_prefix = '/' + self.version + '/'
        self.controller_url = "http://" + address

    def _do_request(self, method, action):
        conn = httplib.HTTPConnection(self.host, self.port)
        url = self.url_prefix + action
        conn.request(method, url)
        res = conn.getresponse()
        if res.status in (httplib.OK,
                          httplib.CREATED,
                          httplib.ACCEPTED,
                          httplib.NO_CONTENT):
            return res

        raise httplib.HTTPException(
            res, 'code %d reason %s' % (res.status, res.reason),
            res.getheaders(), res.read())

    def create_flows(self, switch_id, vlan_id, in_port, uplink):
        # make JSON and then post to the server
        flow_data = {"switch" : switch_id, "vlan" : vlan_id,\
                "ingress-port" : in_port, "uplink" : uplink,\
                "name" : "test"}
        jdata = json.dumps(flow_data)
        urllib2.urlopen(self.controller_url + self.quantum_path, jdata)
        #self._do_request('POST', self.path % (network_id, dpid, port))

    def delete_flows(self, switch_id, vlan_id, in_port, uplink):
        # handle removing of flows, not implemented yet
        print "delete"

def main():
    client = FlClient("localhost")
    client.create_flows("00:00:00:00:00:01", "10", "1", "4")

if __name__ == "__main__":
        main()
