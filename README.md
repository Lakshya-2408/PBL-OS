# Custom Task Manager Pro v2 - Cyber Dark UI + Analytics

Upgraded version with:
- Cyber dark tab-based UI (Dashboard, Analytics, Models, Settings)
- 10 improved categories for process classification
- Collector that logs telemetry to logs/system_data.csv (auto-starts)
- Analytics tab (CPU/Memory trends using Chart.js)
- Model retraining from UI (via endpoints)
- Auto-kill OFF by default

How to run:
1. Extract and open terminal in project folder.
2. Create venv and activate: `python -m venv venv` & `venv\Scripts\activate`
3. Install: `pip install -r requirements.txt`
4. (Optional) Train models: `python train_models.py`
5. Run app: `python -m app.main`
6. Open: http://127.0.0.1:5000/

Prepared for: Lakshya Dhiman
