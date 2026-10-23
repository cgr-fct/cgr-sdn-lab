"""Helpers for building the most common OpenFlow 1.3 messages with os-ken.

You may use these functions as they are, change them, or write your own.
(Same role as last years' SwitchCommands class.)
"""
import csv
import os
import time

import yaml
from os_ken.lib.packet import arp, ethernet, ipv4, packet, tcp, udp


# --------------------------------------------------------------------------- flow entries
def add_flow(datapath, priority, match, actions, idle_timeout=0, hard_timeout=0,
             notify_removal=False, cookie=0):
    """Install (or replace) a flow entry in table 0 of the switch.

    priority        higher wins when several entries match a packet
    match           an OFPMatch, e.g. parser.OFPMatch(in_port=1, eth_dst="00:00:00:00:00:02")
    actions         list of actions, e.g. [parser.OFPActionOutput(2)]; [] means drop
    idle_timeout    seconds without matching packets before the switch removes the entry (0 = never)
    hard_timeout    seconds after which the entry is removed anyway (0 = never)
    notify_removal  ask the switch to send a FLOW_REMOVED message (with the entry's counters)
                    to the controller when the entry is removed (OFPFF_SEND_FLOW_REM flag)
    cookie          64-bit value of your choice, returned in FLOW_REMOVED (useful to tell
                    different kinds of entries apart)
    """
    ofp = datapath.ofproto
    parser = datapath.ofproto_parser
    inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
    flags = ofp.OFPFF_SEND_FLOW_REM if notify_removal else 0
    mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie, priority=priority, match=match,
                            instructions=inst, idle_timeout=idle_timeout,
                            hard_timeout=hard_timeout, flags=flags)
    datapath.send_msg(mod)


def delete_flows(datapath, match, cookie=None):
    """Delete the flow entries that match `match` (and the given cookie, if any)."""
    ofp = datapath.ofproto
    parser = datapath.ofproto_parser
    kw = {}
    if cookie is not None:
        kw = dict(cookie=cookie, cookie_mask=0xFFFFFFFFFFFFFFFF)
    datapath.send_msg(parser.OFPFlowMod(datapath=datapath, command=ofp.OFPFC_DELETE,
                                        out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                                        match=match, **kw))


def install_table_miss(datapath):
    """Lowest-priority entry: send every packet that matches nothing else to the controller."""
    ofp = datapath.ofproto
    parser = datapath.ofproto_parser
    add_flow(datapath, 0, parser.OFPMatch(),
             [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)])


# --------------------------------------------------------------------------- packets
def send_packet_out(datapath, msg, in_port, out_port):
    """Tell the switch to send the packet of a PACKET_IN out of `out_port`
    (use datapath.ofproto.OFPP_FLOOD to send it out of every port except in_port)."""
    ofp = datapath.ofproto
    parser = datapath.ofproto_parser
    data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
    datapath.send_msg(parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port,
                                          actions=[parser.OFPActionOutput(out_port)],
                                          data=data))


class Headers:
    """The headers of a packet, each None if the packet does not have it.

    h = Headers(msg.data)
    h.eth.src, h.eth.dst, h.eth.ethertype
    h.arp.src_ip, h.arp.dst_ip            (ARP)
    h.ip.src, h.ip.dst, h.ip.proto        (IPv4; proto 6 = TCP, 17 = UDP, 1 = ICMP)
    h.tcp.src_port, h.tcp.dst_port, h.tcp.bits  (TCP; h.is_tcp_syn() tells a new connection)
    """

    def __init__(self, data):
        pkt = packet.Packet(data)
        self.eth = pkt.get_protocol(ethernet.ethernet)
        self.arp = pkt.get_protocol(arp.arp)
        self.ip = pkt.get_protocol(ipv4.ipv4)
        self.tcp = pkt.get_protocol(tcp.tcp)
        self.udp = pkt.get_protocol(udp.udp)

    def src_ip(self):
        """Sender IPv4 address of an IPv4 or ARP packet, else None."""
        if self.ip:
            return self.ip.src
        if self.arp:
            return self.arp.src_ip
        return None

    def is_tcp_syn(self):
        """True for the first packet of a TCP connection (SYN set, ACK not set)."""
        return bool(self.tcp and self.tcp.has_flags(tcp.TCP_SYN) and not self.tcp.has_flags(tcp.TCP_ACK))


# --------------------------------------------------------------------------- files
def load_config(path):
    """Read config/limits.yaml. Returns a dict with idle_timeout, tcp_stats_file, limited_hosts."""
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("idle_timeout", 10)
    cfg.setdefault("tcp_stats_file", "tcp_stats.csv")
    cfg["limited_hosts"] = {str(k): int(v) for k, v in (cfg.get("limited_hosts") or {}).items()}
    return cfg


TCP_STATS_FIELDS = ["end_time", "src_ip", "src_port", "dst_ip", "dst_port",
                    "bytes", "packets", "duration_s"]


def append_tcp_stats(path, row):
    """Append one TCP connection record (a dict with the TCP_STATS_FIELDS keys) to the CSV file."""
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    row = dict(row)
    row.setdefault("end_time", time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TCP_STATS_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in TCP_STATS_FIELDS})
