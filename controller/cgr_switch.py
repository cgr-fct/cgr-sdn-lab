"""CGR switch - an os-ken (OpenFlow 1.3) application.

As provided, this application makes every switch behave like a HUB: every packet goes to the
controller (PACKET_IN) and the controller tells the switch to flood it (PACKET_OUT).
Your job is to turn it into the learning switch with a connection limit and TCP statistics
described in STATEMENT.md. Look for the TODO markers.

Run it with:      osken-manager controller/cgr_switch.py
Then, in another terminal:      cgr-net --topo tree,2
"""
import os
import sys

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib.packet import ether_types
from os_ken.ofproto import ofproto_v1_3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofhelpers  # noqa: E402  (helpers next to this file)

CONFIG_FILE = os.environ.get(
    "CGR_CONFIG",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "limits.yaml"))


class CGRSwitch(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ofhelpers.load_config(CONFIG_FILE)
        self.idle_timeout = self.config["idle_timeout"]
        self.limits = self.config["limited_hosts"]          # {"10.0.0.1": 2, ...}
        self.tcp_stats_file = self.config["tcp_stats_file"]
        self.logger.info("CGR switch loaded: idle_timeout=%ss, limited hosts %s, TCP stats in %s",
                         self.idle_timeout, self.limits or "none", self.tcp_stats_file)

        # TODO 1: data structures. At least a MAC table per switch:
        #         self.mac_to_port[dpid][mac] = port
        #         and whatever you need for the connection limit and the TCP statistics.
        self.mac_to_port = {}

    # ------------------------------------------------------------------ switch connects
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.logger.info("switch %016x connected", datapath.id)
        # Entry with priority 0 that sends every unmatched packet to the controller.
        ofhelpers.install_table_miss(datapath)
        # TODO 2 (optional): entries you want in every switch from the start, and resetting
        #         any state you keep about this switch (it may be a new run of cgr-net).

    # ------------------------------------------------------------------ PACKET_IN
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        in_port = msg.match["in_port"]
        h = ofhelpers.Headers(msg.data)

        if h.eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # ignore link-discovery packets

        # TODO 3: learn the port of the source MAC address on this switch.

        # TODO 4: find the output port of the destination MAC address (flood if unknown).
        out_port = ofp.OFPP_FLOOD

        # TODO 5: connection limit. If the source is a limited host (self.limits) that is
        #         already communicating with its maximum number of destinations, and this
        #         packet is for a new destination, drop it (do not send a PACKET_OUT).

        # TODO 6: when the output port is known, install a flow entry so that the next packets
        #         are forwarded by the switch itself, e.g.
        #   match = parser.OFPMatch(in_port=in_port, eth_src=h.eth.src, eth_dst=h.eth.dst)
        #   ofhelpers.add_flow(datapath, 10, match, [parser.OFPActionOutput(out_port)],
        #                      idle_timeout=self.idle_timeout)
        #         Think about which entries the connection limit and the TCP statistics need
        #         (match fields, priorities, idle timeouts, notify_removal, cookies).

        # TODO 7: TCP statistics. When a TCP connection starts (h.is_tcp_syn()), install an
        #         entry for it in ONE switch, with notify_removal=True, to collect its counters.

        # Forward this packet (as a hub: flood).
        ofhelpers.send_packet_out(datapath, msg, in_port, out_port)

    # ------------------------------------------------------------------ FLOW_REMOVED
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        msg = ev.msg
        # Received only for entries installed with notify_removal=True.
        # msg.match, msg.cookie, msg.reason (OFPRR_IDLE_TIMEOUT = 0, OFPRR_HARD_TIMEOUT = 1,
        # OFPRR_DELETE = 2), msg.byte_count, msg.packet_count, msg.duration_sec
        self.logger.info("FLOW_REMOVED switch %016x cookie=%d reason=%d bytes=%d match=%s",
                         msg.datapath.id, msg.cookie, msg.reason, msg.byte_count, msg.match)
        # TODO 8: free the destination of a limited host when its connection ends.
        # TODO 9: write the TCP statistics of a finished connection, e.g.
        #   ofhelpers.append_tcp_stats(self.tcp_stats_file, {"src_ip": ..., "src_port": ...,
        #       "dst_ip": ..., "dst_port": ..., "bytes": ..., "packets": ..., "duration_s": ...})
