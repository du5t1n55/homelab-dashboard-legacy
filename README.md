# homelab-dashboard

Legacy single-host dashboard for the homelab, served by nginx on the monitoring
LXC at `http://192.168.1.127` and protected by Authentik forward-auth
(with a LAN/Tailscale bypass — see `nginx/homelab.conf`).

**Status:** maintenance mode. The primary dashboard has moved to
[homelab-portal](https://github.com/du5t1n55/homelab-portal), served at
`https://homelab-proxy.tail73c4fe.ts.net/portal`. This repo is kept as a
LAN-only fallback that still works when Tailscale or the Authentik outpost is
unavailable.

## Layout

| Path | What it is |
| --- | --- |
| `www/index.html` | Dashboard page (vanilla JS, service launcher + edit modals). |
| `www/services.json` | Service catalog (read/written by `api/main.py`). |
| `api/main.py` | FastAPI service for the editor (CRUD over `services.json`). |
| `nginx/homelab.conf` | nginx site config deployed to `/etc/nginx/sites-enabled/`. |
| `systemd/` | Service units for the FastAPI backend. |
| `deploy.sh` | scp/ssh deploy to 192.168.1.127. |

## Deploy

```bash
bash deploy.sh
```

This rsyncs `www/`, copies `nginx/homelab.conf` to
`/etc/nginx/sites-enabled/`, reloads nginx, and restarts the FastAPI unit.

## License

MIT — see `LICENSE`.
