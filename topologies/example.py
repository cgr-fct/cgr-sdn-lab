"""Example custom topology for cgr-net (Mininet --custom format).

    cgr-net --custom topologies/example.py --topo campus
    cgr-net --custom topologies/example.py --topo campus,3     (3 hosts per access switch)

A core switch s1 with three access switches s2, s3, s4; hosts on the access switches.
No loops: the application learns MAC addresses by flooding, and a loop would make a flooded
broadcast circulate forever (there is no spanning tree here).
"""
from mininet.topo import Topo


class CampusTopo(Topo):
    def build(self, hosts_per_access=2):
        core = self.addSwitch("s1")
        n = 1
        for a in range(2, 5):
            access = self.addSwitch("s%d" % a)
            self.addLink(core, access)
            for _ in range(int(hosts_per_access)):
                h = self.addHost("h%d" % n)
                self.addLink(access, h)
                n += 1


topos = {"campus": CampusTopo}
