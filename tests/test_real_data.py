from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app.main import app
from real_data.banking_pipeline import load_banking
from scripts.real_data.build_transaction_graph import build

client = TestClient(app)

def test_real_data_strategy_explains_label_scope():
    response = client.get('/real-data/strategy')
    assert response.status_code == 200
    data = response.json()
    assert 'not AML' in data['banking']['task']
    assert data['cryptocurrency']['dataset'].startswith('Elliptic')

def test_banking_loader_requires_existing_labels(tmp_path):
    path = tmp_path / 'no_labels.csv'
    pd.DataFrame({'Amount': [1.0, 2.0], 'V1': [0.2, 0.3]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match='No labels are fabricated'):
        load_banking(path)

def test_banking_loader_preserves_existing_class_labels(tmp_path):
    path = tmp_path / 'labeled.csv'
    pd.DataFrame({'Time': [1, 2, 3, 4], 'Amount': [10, 20, 30, 40], 'Class': [0, 1, 0, 1]}).to_csv(path, index=False)
    df, features = load_banking(path)
    assert df['Class'].tolist() == [0, 1, 0, 1]
    assert 'Amount' in features

def test_graph_builder_fails_without_real_entity_columns(tmp_path):
    path = tmp_path / 'transactions.csv'
    pd.DataFrame({'Amount': [10], 'Class': [0]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match='Do not infer or fabricate'):
        build(path, tmp_path / 'graph.json')

def test_graph_builder_uses_supplied_entity_columns(tmp_path):
    path = tmp_path / 'transactions.csv'
    pd.DataFrame({'source_account': ['A', 'A', 'B'], 'destination_account': ['B', 'B', 'C'], 'amount': [10, 15, 8]}).to_csv(path, index=False)
    result = build(path, tmp_path / 'graph.json')
    assert result['nodes'] == 3
    assert result['directed_edges'] == 2
