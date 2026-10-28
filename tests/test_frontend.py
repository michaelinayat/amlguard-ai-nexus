from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_frontend_page_served():
    response = client.get('/ui')
    assert response.status_code == 200
    assert 'AMLGuard AI Nexus' in response.text
    assert 'Crypto investigator' in response.text

def test_frontend_assets_served():
    css = client.get('/ui/styles.css')
    js = client.get('/ui/app.js')
    assert css.status_code == 200 and '--navy' in css.text
    assert js.status_code == 200 and 'refreshStatus' in js.text

def test_full_workspace_views_and_assets_are_present():
    response = client.get('/ui')
    assert response.status_code == 200
    for view in ['view-alerts', 'view-cases', 'view-reports']:
        assert view in response.text
    js = client.get('/ui/app.js').text
    assert 'Save this score as alert' in js
    assert '/workspace/reports/export.csv' in response.text
