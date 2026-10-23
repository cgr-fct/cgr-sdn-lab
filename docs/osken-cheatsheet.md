# os-ken / OpenFlow 1.3 cheat sheet

os-ken is the maintained fork of Ryu (same API, `ryu` → `os_ken`). Reference:
[docs.openstack.org/os-ken](https://docs.openstack.org/os-ken/latest/) — the Ryu book
([book.ryu-sdn.org](https://book.ryu-sdn.org/en/html/)) also applies.

## Application skeleton
```python
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3

class MyApp(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)   # a switch connected
    def features(self, ev): dp = ev.msg.datapath; ...

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)           # PACKET_IN
    def packet_in(self, ev): msg = ev.msg; ...

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)        # FLOW_REMOVED
    def removed(self, ev): msg = ev.msg; ...
```
`self.logger.info("...")` writes to the controller terminal.

## Objects you get
| | |
|---|---|
| `dp = msg.datapath` | the switch; `dp.id` its datapath id (s1 → 1), `dp.ofproto` constants, `dp.ofproto_parser` message classes, `dp.send_msg(m)` |
| `msg.match["in_port"]` | port where the PACKET_IN packet entered |
| `msg.data` | the packet bytes → `ofhelpers.Headers(msg.data)` |
| `msg.buffer_id` | `ofp.OFP_NO_BUFFER` here: the whole packet is in `msg.data` |

## Parsing (ofhelpers.Headers)
```python
h = ofhelpers.Headers(msg.data)
h.eth.src  h.eth.dst  h.eth.ethertype          # ether_types.ETH_TYPE_IP / ETH_TYPE_ARP / ETH_TYPE_LLDP
h.arp.src_ip  h.arp.dst_ip                     # None if not ARP
h.ip.src  h.ip.dst  h.ip.proto                 # in_proto.IPPROTO_TCP (6), IPPROTO_UDP (17), IPPROTO_ICMP (1)
h.tcp.src_port  h.tcp.dst_port  h.is_tcp_syn()
```
(`from os_ken.lib.packet import ether_types, in_proto`)

## Matches (`parser.OFPMatch(...)`)
Fields are keyword arguments; prerequisites must be given (OpenFlow rule: IP fields need
`eth_type=0x0800`, TCP ports need `ip_proto=6` as well).
```python
parser.OFPMatch()                                            # everything
parser.OFPMatch(in_port=1, eth_dst="00:00:00:00:00:02")
parser.OFPMatch(eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.4")
parser.OFPMatch(eth_type=0x0800, ip_proto=6, ipv4_src=..., ipv4_dst=..., tcp_src=..., tcp_dst=...)
match["ipv4_src"]   /   match.get("tcp_dst")                 # read a field (e.g. in FLOW_REMOVED)
```

## Actions
```python
parser.OFPActionOutput(port)                         # a port number
parser.OFPActionOutput(ofp.OFPP_FLOOD)               # all ports except the input port
parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)   # to the controller
[]                                                   # no action = drop
```

## Messages (ofhelpers)
```python
ofhelpers.add_flow(dp, priority, match, actions, idle_timeout=10, hard_timeout=0,
                   notify_removal=True, cookie=2)          # FLOW_MOD add
ofhelpers.delete_flows(dp, match, cookie=None)             # FLOW_MOD delete
ofhelpers.send_packet_out(dp, msg, in_port, out_port)      # PACKET_OUT
ofhelpers.install_table_miss(dp)                           # priority 0 -> controller
```

## FLOW_REMOVED (`ev.msg`)
`msg.cookie`, `msg.priority`, `msg.match`, `msg.reason` (`ofp.OFPRR_IDLE_TIMEOUT`,
`OFPRR_HARD_TIMEOUT`, `OFPRR_DELETE`), `msg.duration_sec`, `msg.duration_nsec`,
`msg.idle_timeout`, `msg.packet_count`, `msg.byte_count`. Only sent for entries installed
with `notify_removal=True`.

## Looking at the switches
```bash
ovs-ofctl -O OpenFlow13 dump-flows s1     # flow table (n_packets, n_bytes, idle_timeout, ...)
ovs-ofctl -O OpenFlow13 show s1           # ports
ovs-vsctl show                            # bridges and controller connection (is_connected)
```
(in the Mininet CLI prefix them with `sh`.)

## Mininet API (custom topologies)
```python
from mininet.topo import Topo
class MyTopo(Topo):
    def build(self):
        s1 = self.addSwitch("s1"); h1 = self.addHost("h1"); self.addLink(s1, h1)
topos = {"mytopo": MyTopo}          # cgr-net --custom file.py --topo mytopo
```
