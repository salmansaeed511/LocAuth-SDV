# EC-DDH (with ZKP) — Density Scenarios + Plots

## Quickstart (Windows PowerShell)
```powershell
cd ecddh-sdv-density-plots
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Open three terminals (activate venv in each):
- A (EAS): `uvicorn edge_auth_server.main:app --reload --host 0.0.0.0 --port 8000`
- B (CGW): `python -m control_gateway.server`
- C (Interactive demo): `python -m tests.demo_scenarios`

The demo asks for the **vehicle density scenario** (frames: 1, 50, 100 or custom).
It saves CSVs to `results/` and PNG plots to `results/plots/`.
