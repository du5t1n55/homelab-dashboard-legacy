from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, uuid, os

DATA_FILE = os.environ.get("SERVICES_FILE", "/var/www/html/services.json")

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
