# Stock Redemption — Next Level

This project is a small warehouse stock lookup UI with a lightweight Flask backend.

Quick start

1. Create a Python virtual environment and activate it (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

4. Open http://127.0.0.1:5000/ in your browser.

What this scaffolds
- `app.py` — minimal Flask app serving `stock.html` and providing `/api/search?q=`.
- `stock_service.py` — core search logic (currently uses in-memory sample data).
- `stock.js` & `stock.html` — frontend updated to call the new API.
- `tests/test_stock_service.py` — simple unit tests for the search logic.

Extended backend

This workspace now contains a lightweight warehouse management backend with:

- JWT-based authentication (`/api/auth/login`, `/api/auth/register`).
- Role-based access control (admin, manager, employee) via decorator.
- SQLAlchemy models for Users, Products, Bins, StockItems, StockMovements, Stocktake records.
- Stock operations endpoints: `/api/stock/receive`, `/api/stock/dispatch`, `/api/stock/transfer`, `/api/stock/items`.
- Bin and product management endpoints.
- DB initialization endpoint: `POST /api/init-db` to create tables and seed an `admin` user.

Run the system

1. Create and activate a venv (PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize DB (creates `wms.db` and seeds admin):

```powershell
curl -X POST http://127.0.0.1:5000/api/init-db
```

Or run in PowerShell after starting the app.

4. Run the app:

```powershell
python app.py
```

Default admin credentials: `admin` / `adminpass` (change immediately in production).


Next steps you might want
- Replace in-memory data with a database (SQLite/Postgres) or an API.
- Add authentication and role-based UI.
- Add pagination, export, and CSV import for inventory.
