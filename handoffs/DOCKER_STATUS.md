# Docker status on the box (2026-11-03, PKT)

Result: Docker compose E2E PASSES on the box, with one box-specific override.

## What was installed
- Docker 27.3.1 static binaries from download.docker.com into /usr/local/bin (apt mirror returned HTTP 500 / SSL EOF).
- Docker Compose v2.29.7 plugin in /usr/local/lib/docker/cli-plugins.

## Box limitation
- iptables is not installed and the apt mirror fails to deliver it, so dockerd runs as:
  `sudo dockerd --iptables=false &`
- Without iptables, bridge network DNS (service name `postgres`) fails, so the stock compose file
  cannot start the API. `docker-compose.box.yml` switches all services to host networking.
  Host ports are unchanged: API 8010, web 3010.
- dockerd is not a service; it must be restarted manually after a box reboot.

## How to run
    sudo dockerd --iptables=false > /tmp/dockerd.log 2>&1 &
    sudo docker compose -f docker-compose.yml -f docker-compose.box.yml up --build -d
    scripts/smoke-local.sh

## Evidence
/workspace/godmode/refs/compose-e2e-*/ (versions, compose ps, curl, smoke outputs)

## Findings
- Admin seed reads GODMODE_ADMIN_EMAIL / GODMODE_ADMIN_PASSWORD (default godmode123).
  compose and .env.example set SEED_ADMIN_* which the API ignores. Not changed here.
- Stock compose (bridge networking) is still unverified on a host with iptables.
