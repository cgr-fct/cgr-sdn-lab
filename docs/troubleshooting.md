# Troubleshooting

**VS Code does not offer "Reopen in Container" / "Docker is not running".**
Start Docker Desktop (Windows/macOS) and wait for *Engine running*; on Linux check
`docker run hello-world` works without sudo. Then F1 → *Dev Containers: Reopen in Container*.

**The image cannot be downloaded (`ghcr.io/cgr-fct/cgr-sdn`).**
Check the Internet connection (a VPN can block it). As an alternative you can build the
image on your computer (takes a few minutes): in `.devcontainer/devcontainer.json` replace
the `"image": …` line by
`"build": { "dockerfile": "../image/Dockerfile", "context": ".." },`
and run F1 → *Dev Containers: Rebuild Container*.

**`cgr-net` hangs at `*** Starting 3 switches`.** The switch daemon `ovs-vswitchd` is not
running (only the database is: `pgrep -a ovs`). Press Ctrl-C, run `cgr-net --clean`, then
`start-ovs`, and start `cgr-net` again. (The lab's switches run in userspace, so the
"Module openvswitch not found" message of the standard OVS start script is harmless.)

**`Open vSwitch did not start` / `ovs-vsctl: unix:/var/run/openvswitch/db.sock: database
connection failed`.**
Run `start-ovs` in a container terminal. If it still fails, the container is not running
with `--privileged`: do not remove `runArgs` from `devcontainer.json`, and rebuild
(F1 → *Dev Containers: Rebuild Container*).

**`port 6653 is already in use`.**
Another controller is still running (maybe in another terminal or the debugger). Stop it
with Ctrl-C in its terminal, or `pkill -f osken-manager`.

**The switches do not connect (`Not all switches are connected`, the controller log shows
nothing).**
Start the controller first (`osken-manager controller/cgr_switch.py`) and check it did not
stop with a Python error (the traceback is in its terminal). The switches keep trying to
connect, so you can also start the controller after the network.

**`cgr-net` fails with `File exists` / an old network is still there.**
A previous run did not stop cleanly: `cgr-net --clean`, then start it again.

**pingall works but TCP (iperf3, curl) does not.**
Start the network with `cgr-net` (it disables checksum offloading on the hosts, which the
userspace switches need). If you build your own Mininet script, do the same:
`h.cmd('ethtool -K %s-eth0 tx off rx off' % h.name)` for every host. If it still fails,
check your flow entries for TCP.

**Changes in `cgr_switch.py` have no effect.**
The controller reads the file when it starts: stop it (Ctrl-C) and start it again. Changes
in `config/limits.yaml` also need a restart.

**Breakpoints are not hit.**
Start the controller with *Run → Start Debugging* (configuration *Debug controller*), not in
a terminal, and stop any other controller first (only one can listen on port 6653).

**Windows: Docker Desktop and VMware Workstation.** VMware Workstation 17 and later run with
WSL 2 / Hyper-V enabled; if an older VMware stops working after installing Docker Desktop,
update it.
