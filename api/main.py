from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, uuid, os, urllib.parse, urllib.request

DATA_FILE = os.environ.get("SERVICES_FILE", "/var/www/html/services.json")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090")

app = FastAPI(title="Homelab Dashboard API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


class ServiceIn(BaseModel):
    name: str
    url: str
    tag: str = ""
    icon: str = ""
    tags: str = ""

class SectionIn(BaseModel):
    title: str


@app.get("/api/services")
def get_services():
    return load()


# ── Stats (read-only Prometheus summary) ─────────────────────────────────────
# Mirrors the tile set on the homelab-portal dashboard. Queries the Prometheus
# running alongside us on this host (PROMETHEUS_URL, default localhost:9090),
# so it needs no auth and stays on the box.
TILE_QUERIES = {
    "cpu_pct":      '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "mem_pct":      '(1 - (avg(node_memory_MemAvailable_bytes) / avg(node_memory_MemTotal_bytes))) * 100',
    "disk_pct":     'max(100 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"} * 100 / node_filesystem_size_bytes))',
    "net_rx_mbps":  'sum(rate(node_network_receive_bytes_total{device!~"lo|docker.*|veth.*|tailscale.*"}[5m])) * 8 / 1024 / 1024',
    "targets_up":   'sum(up == 1)',
    "targets_down": 'sum(up == 0)',
}


def _prom_query(expr: str):
    url = f"{PROMETHEUS_URL}/api/v1/query?" + urllib.parse.urlencode({"query": expr})
    with urllib.request.urlopen(url, timeout=4) as r:
        result = json.load(r).get("data", {}).get("result", [])
    return float(result[0]["value"][1]) if result else None


@app.get("/api/stats")
def get_stats():
    out = {}
    for key, expr in TILE_QUERIES.items():
        try:
            out[key] = _prom_query(expr)
        except Exception:
            out[key] = None
    return out


@app.post("/api/sections")
def add_section(sec: SectionIn):
    data = load()
    sec_id = sec.title.lower().replace(" ", "-")
    if any(s["id"] == sec_id for s in data["sections"]):
        raise HTTPException(409, "Section already exists")
    entry = {"id": sec_id, "title": sec.title, "services": []}
    data["sections"].append(entry)
    save(data)
    return entry


@app.delete("/api/sections/{section_id}")
def delete_section(section_id: str):
    data = load()
    before = len(data["sections"])
    data["sections"] = [s for s in data["sections"] if s["id"] != section_id]
    if len(data["sections"]) == before:
        raise HTTPException(404, "Section not found")
    save(data)
    return {"ok": True}


@app.post("/api/sections/{section_id}/services")
def add_service(section_id: str, svc: ServiceIn):
    data = load()
    for section in data["sections"]:
        if section["id"] == section_id:
            entry = {**svc.model_dump(), "id": str(uuid.uuid4())[:8]}
            section["services"].append(entry)
            save(data)
            return entry
    raise HTTPException(404, "Section not found")


@app.put("/api/sections/{section_id}/services/{service_id}")
def update_service(section_id: str, service_id: str, svc: ServiceIn):
    data = load()
    for section in data["sections"]:
        if section["id"] == section_id:
            for i, s in enumerate(section["services"]):
                if s["id"] == service_id:
                    section["services"][i] = {**svc.model_dump(), "id": service_id}
                    save(data)
                    return section["services"][i]
    raise HTTPException(404, "Service not found")


@app.delete("/api/sections/{section_id}/services/{service_id}")
def delete_service(section_id: str, service_id: str):
    data = load()
    for section in data["sections"]:
        if section["id"] == section_id:
            before = len(section["services"])
            section["services"] = [s for s in section["services"] if s["id"] != service_id]
            if len(section["services"]) == before:
                raise HTTPException(404, "Service not found")
            save(data)
            return {"ok": True}
    raise HTTPException(404, "Section not found")
