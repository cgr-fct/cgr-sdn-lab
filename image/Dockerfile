# CGR SDN lab image: Mininet + Open vSwitch (userspace datapath) + os-ken (OpenFlow 1.3).
# Built for linux/amd64 and linux/arm64 by .github/workflows/image.yml and published as
#   ghcr.io/cgr-fct/cgr-sdn:latest
# Local build (from the repository root):  docker build -t cgr-sdn -f image/Dockerfile .
FROM ubuntu:24.04

LABEL org.opencontainers.image.source="https://github.com/cgr-fct/cgr-sdn-lab" \
      org.opencontainers.image.description="CGR SDN lab: os-ken + Mininet + Open vSwitch"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        mininet openvswitch-switch openvswitch-common \
        python3 python3-pip python3-yaml \
        iproute2 iputils-ping iperf3 tcpdump ethtool net-tools curl \
        procps psmisc less nano vim-tiny git zip unzip ca-certificates bash-completion \
    && rm -rf /var/lib/apt/lists/*

# os-ken (the maintained fork of Ryu) and the VS Code Python debugger
RUN pip3 install --no-cache-dir "os-ken==4.2.2" debugpy

# Lab tools: osken-manager, cgr-net, hsh, start-ovs
COPY image/bin/ /usr/local/bin/
RUN chmod +x /usr/local/bin/* \
    && echo 'cgr-sdn-lab image' > /etc/cgr-sdn-release

WORKDIR /workspaces
CMD ["sleep", "infinity"]
