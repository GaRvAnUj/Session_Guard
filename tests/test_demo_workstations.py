import os
import sys

from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.server_runner import app


def test_demo_workstations_are_listed_as_active():
    with TestClient(app) as client:
        login = client.post("/api/admin/login", json={"username": "admin", "password": "admin"})
        admin_headers = {"Authorization": "Bearer " + login.json()["token"]}

        response = client.get("/api/sessions/active", headers=admin_headers)

    assert response.status_code == 200
    machine_ids = {session["machineId"] for session in response.json()}
    assert {"PC_LAB_03", "PC_LAB_05"} <= machine_ids
