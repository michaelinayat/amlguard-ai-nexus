# Current public-data edition evidence

- `api_evidence.json`: output captured from the local FastAPI TestClient for health, root, strategy, and disabled legacy synthetic scoring.
- `test_output.txt`: local automated test run output.
- `01_real_data_strategy.png` and `02_tests.png`: readable visual renderings of those outputs for the certification presentation. These are generated evidence panels, not screenshots of a deployed production service.

Actual dataset training metrics are intentionally not included because raw datasets were not downloaded into this environment. Run the two training commands after acquiring the datasets to generate authentic evaluation JSON.
