# CGR 2026/2027 — 2nd Project: Software Defined Networks exercise

**Configuração e Gestão de Redes** · DEE – FCT NOVA · Pedro Amaral (pfa@fct.unl.pt)

## 1. Overview

In this exercise you program the **control plane** of a network. You write an SDN application
for the **os-ken** controller (the maintained, Python successor of the Ryu controller) that
controls a network of **OpenFlow 1.3** switches. The switches are **Open vSwitch** bridges in a
network emulated by **Mininet**, all running in one container on your computer.

Your application makes the switches work as **learning switches**, and adds two features:

* **Connection limitation** — some hosts may only communicate with a limited number of
  destinations at the same time. A new destination is allowed again only when one of the
  previous ones has stopped communicating for a while.
* **TCP traffic data collection** — the byte count and the duration of every TCP connection
  are written to a CSV file.

The controller learns about packets that the switches cannot handle (OpenFlow `PACKET_IN`),
decides what to do, and tells the switches either how to forward that single packet
(`PACKET_OUT`) or how to forward all the following packets of the same kind (a flow entry
installed with `FLOW_MOD`). Switches report flow entries that expire (`FLOW_REMOVED`).

## 2. Setup

You need **Docker** and **VS Code**:

| Your computer | Install |
|---|---|
| Windows 10/11 | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (it uses WSL 2; free for students) |
| macOS (Intel or Apple Silicon) | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| Linux | Docker Engine (`sudo apt install docker.io`, or [docs.docker.com/engine/install](https://docs.docker.com/engine/install/)) and add your user to the `docker` group |

Then install [VS Code](https://code.visualstudio.com/) and its **Dev Containers** extension
(`ms-vscode-remote.remote-containers`).

1. Clone the lab repository: `git clone https://github.com/cgr-fct/cgr-sdn-lab.git`
   (or *Code → Download ZIP* on GitHub and unzip it).
2. Start Docker Desktop (Windows/macOS) and open the `cgr-sdn-lab` folder in VS Code.
3. Accept **Reopen in Container** (or press F1 → *Dev Containers: Reopen in Container*).
   The first time, VS Code downloads the lab image (about 120 MB). Then you have a terminal
   *inside* the container, as root, in `/workspaces/cgr-sdn-lab`.

Step-by-step details and solutions to common problems: [docs/setup.md](docs/setup.md) and
[docs/troubleshooting.md](docs/troubleshooting.md).

## 3. Working in the container

Use two VS Code terminals (the **+** button in the terminal panel):

| Terminal | Command | What it does |
|---|---|---|
| 1 | `osken-manager controller/cgr_switch.py` | runs your application; its log appears here. Stop it with Ctrl-C, start it again after each change. |
| 2 | `cgr-net --topo tree,2` | starts a Mininet network whose switches connect to the controller (127.0.0.1:6653) and opens the Mininet CLI. `exit` stops the network. |
| 3 (optional) | `hsh h1` | a shell on host h1 (to run tcpdump, iperf3, … while the network runs) |

Topologies: `--topo tree,2` (3 switches, 4 hosts — the default), `tree,3`, `linear,4`,
`single,5`, or your own file: `cgr-net --custom topologies/example.py --topo campus`.
Hosts are `h1, h2, …` with IP `10.0.0.N` and MAC `00:00:00:00:00:0N`.

Useful commands in the Mininet CLI:

```
mininet> pingall                                   # every host pings every other host
mininet> h1 ping -c 3 h4
mininet> h4 iperf3 -s -D                           # TCP server on h4 (background)
mininet> h1 iperf3 -c h4 -t 5                      # 5 s TCP transfer h1 -> h4
mininet> h1 curl -s http://10.0.0.4:8000/          # after: h4 python3 -m http.server 8000 &
mininet> sh ovs-ofctl -O OpenFlow13 dump-flows s1  # the flow table of switch s1
mininet> links / net / dump                        # how the network is connected
```

From a shell on a host (`hsh h2`): `tcpdump -n -i h2-eth0` shows the packets the host sees.

To debug, use *Run → Start Debugging* (configuration **Debug controller**): breakpoints in
`cgr_switch.py` stop the controller when a packet arrives.

## 4. The starting application

`controller/cgr_switch.py` is provided. As it is, it makes every switch a **hub**: every
packet is sent to the controller, which tells the switch to flood it. Start by running it,
building the network and checking the hub behaviour: everything works, but with `hsh` and
`tcpdump` on two hosts you can see that every host receives every packet, and the flow tables
(`dump-flows`) only have the entry that sends packets to the controller.

`controller/ofhelpers.py` has ready-to-use functions for the most common OpenFlow messages
(`add_flow`, `delete_flows`, `send_packet_out`), to parse packets (`Headers`), to read the
configuration and to write the CSV file. [docs/osken-cheatsheet.md](docs/osken-cheatsheet.md)
summarises the os-ken API you need.

`config/limits.yaml` is read when the controller starts:

```yaml
idle_timeout: 10              # seconds
tcp_stats_file: tcp_stats.csv
limited_hosts:                # IPv4 address: maximum simultaneous destinations
  10.0.0.1: 2
  10.0.0.3: 1
```

## 5. Specification

### 5.1 Learning switch

The application keeps, for each switch, a **MAC table** that maps MAC addresses to the port
where they were learned. When a packet arrives at the controller, the mapping *source MAC →
input port* is stored. If the destination MAC is known, the packet is sent only to that
port; otherwise it is flooded.

When the destination port is known, the controller can handle the packet in two ways:

1. Tell the switch to send that packet to the port (`PACKET_OUT`).
2. Also install a flow entry (`FLOW_MOD`) so that the switch forwards the following packets of
   that communication by itself.

The second is required: it reduces the communication between the switches and the controller.
Flow entries must have an **idle timeout**, so the tables do not grow forever.

### 5.2 Connection limitation

Hosts listed in `limited_hosts` may communicate with at most their limit of **destinations at
the same time**. Hosts that are not listed have no limit. A destination is *in use* while
there is traffic from the limited host to it; it stops being in use when that traffic has
stopped for `idle_timeout` seconds. Only IPv4 traffic counts (ARP is always allowed).

Example: `10.0.0.1: 2`. Host h1 pings h2 and h3 continuously. A ping from h1 to h4 now fails
(its packets are dropped). When one of the first two pings stops, h1 can ping h4 after at
most `idle_timeout` seconds.

### 5.3 TCP statistics

For every TCP connection, the **byte count** and the **duration** must be written to the CSV
file `tcp_stats_file`, one line per connection (direction), with the columns:

`end_time, src_ip, src_port, dst_ip, dst_port, bytes, packets, duration_s`

The controller must detect when a TCP connection begins and install, at that moment, a flow
entry that matches that connection in **one** of the switches it crosses, so that the
switch counts its packets and bytes. When the entry expires, the switch reports its counters
(`FLOW_REMOVED`) and the controller writes the line.

### 5.4 General requirements

* All the features must work **whatever the topology** (loop-free; there is no spanning tree,
  so in a topology with loops the flooded broadcasts would circulate forever). Assume the
  topology does not change while the controller runs.
* In a multi-switch topology the same packet crosses several switches, all controlled by the
  same application: make sure that a limit is enforced once and that each TCP connection is
  counted once.
* The configuration (limits, idle timeout, file name) is read from `config/limits.yaml`; the
  application must not have addresses written in the code.

## 6. Hints

* Start from the hub. Then add the MAC learning with `PACKET_OUT` only, then the flow entries.
  Check the flow tables with `dump-flows` after each step.
* A flow entry is chosen by its **priority** when several match a packet. Think about what
  each kind of entry must match (`in_port`, `eth_src`, `eth_dst`, `ipv4_src`, `ipv4_dst`,
  `ip_proto`, `tcp_src`, `tcp_dst`, …): an entry that is too general makes the switch forward
  packets that the controller should have seen (a new destination of a limited host, the
  first packet of a new TCP connection).
* `idle_timeout` and the `notify_removal` flag (`OFPFF_SEND_FLOW_REM`) are the tools for both
  features: the controller is told when an entry expires, with its counters. Use the
  **cookie** to tell your kinds of entries apart in `FLOW_REMOVED`.
* `FLOW_REMOVED` reports `duration_sec`, the time the entry existed. Is that the duration of
  the connection?
* The first packet of a TCP connection has the SYN flag set and ACK not set
  (`Headers.is_tcp_syn()`).
* Test with more than one topology, with hosts on the same switch and on different switches.

## 7. What to deliver

Only your files, in one zip named after your group, uploaded as explained on the course page:

* `controller/cgr_switch.py` (and any other `.py` modules you created in `controller/`);
* `config/limits.yaml`;
* any topology files you used for testing (`topologies/*.py`).

No report. Write a short comment at the top of `cgr_switch.py` with the group number and
names. Your files must work in a fresh copy of this repository, with the commands of
Section 3. Do not publish your work in a public repository or a public fork (other groups
would see it).

## 8. Evaluation

The exercise is evaluated in a **discussion** with the group (together with the other
exercises of the project). Your files are copied into a fresh copy of the repository and run
on a topology you have not seen, with a different `limits.yaml`. Each member will be asked
to explain the design (which entries, which matches, which priorities and timeouts, and why),
to predict what will happen in a given situation and check it, and to make a small change to
the application or the configuration during the discussion.
