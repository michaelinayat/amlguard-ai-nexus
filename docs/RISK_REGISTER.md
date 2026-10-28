# Risk Register — Public Real-Data Edition

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | Public banking dataset labels card fraud, not AML | Critical | Name the task card-fraud proxy; do not claim AML validity. Obtain authorized investigator-labeled bank AML data for that task. |
| R2 | Dataset license unclear or restrictive | High | Verify exact version/provider terms; record rights in the dataset manifest; do not redistribute raw data without permission. |
| R3 | Elliptic labels incomplete or imperfect | High | Exclude unknown labels from supervised metrics; document label provenance and limitations; human review. |
| R4 | Temporal or graph feature leakage | High | Use time-aware split; audit aggregated features and prediction-time availability; report caveats. |
| R5 | Class imbalance hides poor minority recall | High | Report average precision/PR-AUC, recall, precision, F1, confusion matrix and class support, not accuracy alone. |
| R6 | Card-fraud data lacks account IDs for graph construction | Medium | Do not invent entities/edges; use graph builder only on datasets with genuine source/destination IDs. |
| R7 | False positives harm customers | Critical | No automated adverse actions; human investigation, governance, appeal and escalation process required. |
| R8 | Data leakage or privacy violation | Critical | Do not include raw data in repository/ZIP; follow provider terms, least privilege, retention controls and applicable law. |
| R9 | Domain shift across coins, banks, products and time | High | Dataset-specific validation, drift monitoring and revalidation before deployment. |
| R10 | Model score misinterpreted as proof | Critical | User-facing disclaimers; score is triage signal only, never evidence of guilt by itself. |
