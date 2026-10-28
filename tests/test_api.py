from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_root_discloses_public_data_mode():
    data = client.get('/').json()
    assert 'public-data' in data['mode']
    assert 'disabled' in data['legacy_demo']

def test_legacy_synthetic_score_is_disabled():
    r = client.post('/score', json={'transaction_id':'T-1'})
    assert r.status_code == 410
    assert 'synthetic' in r.json()['detail'].lower()

def test_legacy_synthetic_summary_is_disabled():
    r = client.get('/dataset/summary')
    assert r.status_code == 410

def test_real_data_strategy_explains_scope():
    data = client.get('/real-data/strategy').json()
    assert 'not AML' in data['banking']['task']
    assert data['cryptocurrency']['dataset'].startswith('Elliptic')
