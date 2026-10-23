# Setup

The whole lab (controller, Mininet, Open vSwitch) runs in one Docker container that VS Code
opens for you. Nothing else is installed on your computer.

## 1. Docker

### Windows 10/11
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (free for students).
   Accept the **WSL 2** option; if Windows asks, let it install WSL 2 and restart.
2. Start Docker Desktop and wait until it shows *Engine running*.

### macOS (Intel or Apple Silicon)
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) — choose the
   *Apple Silicon* or *Intel chip* download that matches your Mac.
2. Start Docker Desktop and wait until it shows *Engine running*.

### Linux
1. Install Docker Engine: `sudo apt install docker.io` (Ubuntu/Debian) or follow
   [docs.docker.com/engine/install](https://docs.docker.com/engine/install/).
2. `sudo usermod -aG docker $USER`, then log out and in again. `docker run hello-world`
   must work without `sudo`.

## 2. VS Code
1. Install [VS Code](https://code.visualstudio.com/).
2. Install the **Dev Containers** extension (Extensions panel → search *Dev Containers*,
   publisher Microsoft).

## 3. The lab repository
```bash
git clone https://github.com/cgr-fct/cgr-sdn-lab.git
```
(or *Code → Download ZIP* on GitHub and unzip it). Open the `cgr-sdn-lab` folder in VS Code
(*File → Open Folder*). VS Code offers **Reopen in Container**: accept (or F1 →
*Dev Containers: Reopen in Container*).

The first time VS Code downloads the image `ghcr.io/cgr-fct/cgr-sdn` (about 120 MB) and
installs the Python extension inside the container; after that it opens in seconds. The
bottom-left corner shows *Dev Container: CGR SDN lab*. A terminal (Terminal → New Terminal)
is a root shell *inside* the container, in `/workspaces/cgr-sdn-lab`, and the message
*Open vSwitch started* appeared when the container started.

Your files stay in the folder on your computer (the container only mounts it): what you
edit in VS Code is saved there.

## 4. Check that everything works
Terminal 1:
```bash
osken-manager controller/cgr_switch.py
```
Terminal 2:
```bash
cgr-net --test pingall
```
The last lines must show `Results: 0% dropped (12/12 received)`, and terminal 1 shows the
three switches connecting. You are ready to start the exercise (STATEMENT.md).

Next time: start Docker Desktop, open the folder in VS Code; it reopens the container.
