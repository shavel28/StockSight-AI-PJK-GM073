# StockSight AI — Backend API

FastAPI backend untuk proyek Capstone **PJK-GM073**.  
Stack: **FastAPI · PostgreSQL · Prophet/ARIMA · JWT Auth**

---

## Struktur Project

```
stocksight-api/
├── app/
│   ├── main.py                  # Entry point FastAPI
│   ├── api/v1/
│   │   ├── router.py            # Agregator semua router
│   │   └── endpoints/
│   │       ├── auth.py          # POST /register, /login, GET /me
│   │       ├── uploads.py       # Upload & pipeline CSV
│   │       ├── products.py      # CRUD produk & sales
│   │       ├── forecasts.py     # Trigger & ambil hasil ML
│   │       └── inventory_dashboard.py  # Reorder, alert, summary
│   ├── core/
│   │   ├── config.py            # Settings dari .env
│   │   └── security.py          # JWT & password hashing
│   ├── db/
│   │   └── session.py           # Async SQLAlchemy engine
│   ├── models/
│   │   └── models.py            # ORM: User, Upload, Product, ...
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response
│   └── services/
│       ├── user_service.py      # DB ops untuk user
│       ├── pipeline_service.py  # Validasi & ingest CSV
│       ├── forecast_service.py  # Prophet & ARIMA engine
│       └── inventory_service.py # Reorder point & alert
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup & Menjalankan

### 1. Clone & install dependencies

```bash
cd stocksight-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Konfigurasi environment

```bash
cp .env
# Edit .env: isi DATABASE_URL dan SECRET_KEY
```

### 3. Pastikan PostgreSQL berjalan, lalu jalankan API

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Buka dokumentasi interaktif

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

---

## Alur Penggunaan API

```
1. POST /api/v1/auth/register   → buat akun
2. POST /api/v1/auth/login      → dapat JWT token
3. POST /api/v1/uploads         → upload CSV penjualan (async pipeline)
4. GET  /api/v1/uploads/:id     → cek status pipeline (pending/done/error)
5. GET  /api/v1/products        → lihat produk hasil parsing
6. POST /api/v1/forecasts       → trigger forecasting Prophet/ARIMA (async)
7. GET  /api/v1/forecasts/:id/details → ambil prediksi harian
8. GET  /api/v1/inventory/reorder    → reorder point & safety stock
9. GET  /api/v1/dashboard/summary    → ringkasan untuk dashboard
```

---

## Format CSV yang Didukung

| Kolom           | Tipe       | Wajib |
| --------------- | ---------- | ----- |
| `product_name`  | string     | Ya    |
| `sale_date`     | YYYY-MM-DD | Ya    |
| `quantity_sold` | integer    | Ya    |
| `revenue`       | float      | Tidak |
| `category`      | string     | Tidak |
| `region`        | string     | Tidak |

---

## Job Desk Integrasi Tim

| Anggota          | Tugas utama di codebase                       |
| ---------------- | --------------------------------------------- |
| Arizal (Backend) | `main.py`, semua `endpoints/`, `security.py`  |
| Shava (Data Eng) | `pipeline_service.py`, `inventory_service.py` |
| Dianwan (ML Eng) | `forecast_service.py` — Prophet & ARIMA       |
| Rania (Frontend) | Konsumsi endpoint ini via React               |
| Farkhan (PM)     | Dokumentasi, testing, koordinasi              |
