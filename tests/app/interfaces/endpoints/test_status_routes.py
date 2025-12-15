from fastapi.testclient import TestClient


def test_get_status(client: TestClient):
    response = client.get('/api/status')
    data = response.json()

    assert response.status_code == 200
    assert data.get('code') == 200
