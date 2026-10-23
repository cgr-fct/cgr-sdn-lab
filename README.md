# CGR SDN lab — os-ken + Mininet

Lab environment of the SDN exercise of the 2nd project of **Configuração e Gestão de Redes**
(DEE – FCT NOVA). You write an OpenFlow 1.3 application for the
[os-ken](https://opendev.org/openstack/os-ken) controller and test it on networks of
Open vSwitch switches emulated by Mininet — all in one container opened by VS Code.

**→ The assignment: [STATEMENT.md](STATEMENT.md)**

## Quick start
1. Install Docker Desktop (Windows, macOS) or Docker Engine (Linux), VS Code and the VS Code
   **Dev Containers** extension — [docs/setup.md](docs/setup.md).
2. `git clone https://github.com/cgr-fct/cgr-sdn-lab.git`, open the folder in VS Code and
   choose **Reopen in Container**.
3. In two terminals of the container:
   ```bash
   osken-manager controller/cgr_switch.py      # terminal 1: the controller
   cgr-net --topo tree,2                       # terminal 2: the network + Mininet CLI
   ```
   `hsh h1` (in a third terminal) opens a shell on host h1.

## What is here
| | |
|---|---|
| `controller/cgr_switch.py` | the application you develop (starts as a hub) |
| `controller/ofhelpers.py` | helpers for OpenFlow messages, packet parsing, config and CSV |
| `config/limits.yaml` | idle timeout, limited hosts, CSV file name |
| `topologies/example.py` | example custom topology (`cgr-net --custom topologies/example.py --topo campus`) |
| `docs/` | [setup](docs/setup.md) · [os-ken cheat sheet](docs/osken-cheatsheet.md) · [troubleshooting](docs/troubleshooting.md) |
| `image/` | how the container image is built (Ubuntu 24.04, Mininet 2.3, Open vSwitch 3.3, os-ken 4.2) and the lab commands `osken-manager`, `cgr-net`, `hsh`, `start-ovs` |
| `.devcontainer/` | VS Code dev container definition |
