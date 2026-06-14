# StockSight AI — Backend API

> **PJK-GM073** · Peramalan Deret Waktu (*Time Series Forecasting*) & Kecerdasan Inventori untuk UMKM Indonesia

Layanan backend untuk StockSight AI, dibangun menggunakan **FastAPI** dan **PostgreSQL**. Backend ini menangani seluruh alur mulai dari pengunggahan (*ingestion*) CSV mentah hingga peramalan permintaan bertenaga ML — termasuk pengayaan Data Engineering (DE) otomatis (deteksi hari libur, penandaan hari gajian, pembatasan pencilan) dan dua mesin peramalan: **Prophet** dan **ARIMA**.

---

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Stack Teknologi](#stack-teknologi)
- [Struktur Proyek](#struktur-proyek)
- [Langkah Memulai](#langkah-memulai)
- [Alur Penggunaan API](#alur-penggunaan-api)
- [Format CSV yang Didukung](#format-csv-yang-didukung)
- [Integrasi DE + ML](#integrasi-de--ml)

---

## Fitur Utama

### Pengayaan Fitur Otomatis (DE Pipeline)

Ketika file CSV diunggah, backend secara otomatis memperkaya data sebelum dikirim ke lapisan ML:

| Fitur | Deskripsi |
| :--- | :--- |
| **Deteksi Hari Libur Nasional** | Mendeteksi hari libur nasional Indonesia untuk semua tahun dalam dataset menggunakan `holidays.Indonesia` |
| **Penandaan Hari Gajian (Payday)**| Menandai jendela hari gajian (tanggal 25–31 dan 1–3 setiap bulan) sebagai `is_payday` |
| **IQR Outlier Capping** | Membatasi nilai `quantity_sold` yang ekstrem per produk menggunakan ambang batas $Q3 + 1.5 \times IQR$ |
| **Pemetaan Format Colab** | Secara otomatis memetakan kolom dari file ekspor Colab (`ds`, `Category`, `y_capped`) ke skema backend |

### Mesin Peramalan ML dengan Regressor Eksternal

Kedua model peramalan mengintegrasikan fitur `is_holiday` dan `is_payday` sebagai masukan eksternal:

- **Prophet** — melalui `model.add_regressor()`, dengan proyeksi otomatis fitur masa depan
- **ARIMA / SARIMAX** — melalui parameter `exog`, dengan variabel eksogen masa depan yang cocok

### Migrasi Database Otomatis saat Startup

Aplikasi menambahkan kolom `is_holiday` dan `is_payday` ke tabel `sales_records` secara otomatis pada saat pertama kali dijalankan — tidak memerlukan langkah migrasi manual.

---

## Stack Teknologi

| Lapisan | Teknologi |
| :--- | :--- |
| Web Framework | FastAPI |
| Database | PostgreSQL (asinkron via `asyncpg`) |
| ORM | SQLAlchemy (asinkron) |
| Peramalan (ML) | Prophet · statsmodels (SARIMAX) |
| Autentikasi | JWT (python-jose) · bcrypt |
| Feature Engineering | holidays · pandas |
| Validasi | Pydantic v2 |

---

## Struktur Proyek

```
stocksight-api/
├── app/
│   ├── main.py                         # Entry point FastAPI & migrasi lifespan startup
│   ├── api/v1/
│   │   ├── router.py                   # Agregator rute/endpoint
│   │   └── endpoints/
│   │       ├── auth.py                 # POST /register, /login · GET /me
│   │       ├── uploads.py              # Upload CSV & trigger pipeline DE
│   │       ├── products.py             # Endpoint produk & riwayat penjualan
│   │       ├── forecasts.py            # Trigger & hasil forecast ML
│   │       └── inventory_dashboard.py  # Reorder alert & ringkasan dasbor
│   ├── core/
│   │   ├── config.py                   # Pengaturan aplikasi (dimuat dari .env)
│   │   └── security.py                 # Pembuatan JWT & hashing kata sandi
│   ├── db/
│   │   └── session.py                  # Async SQLAlchemy engine & session
│   ├── models/
│   │   └── models.py                   # Model ORM: User, Upload, Product, SalesRecord, Forecast
│   ├── schemas/
│   │   └── schemas.py                  # Skema request/response Pydantic
│   └── services/
│       ├── pipeline_service.py         # Validasi CSV, pemetaan Colab & enrich_features()
│       ├── forecast_service.py         # Mesin Prophet & ARIMA dengan regressors/exog
│       ├── inventory_service.py        # Kalkulasi Reorder Point & Safety Stock
│       └── user_service.py             # Operasi database untuk User
├── .env.example
├── requirements.txt
└── README.md
```

---

## Langkah Memulai

### Prasyarat

- Python 3.10+
- PostgreSQL 14+

### Instalasi

```bash
# 1. Clone repositori
git clone https://github.com/shavel28/StockSight-AI-PJK-GM073.git
cd StockSight-AI-PJK-GM073

# 2. Buat dan aktifkan virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependensi
pip install -r requirements.txt

# 4. Konfigurasi environment variables
cp .env.example .env
# Edit berkas .env — sesuaikan isi DATABASE_URL dan SECRET_KEY
```

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/stocksight
SECRET_KEY=kunci_rahasia_anda_di_sini
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
```

### Jalankan API

```bash
uvicorn app.main:app --reload --port 8000
```

| Antarmuka | URL |
| :--- | :--- |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Alur Penggunaan API

Alur penggunaan umum dari ujung-ke-ujung (end-to-end) bagi pengguna baru:

```
1.  POST /api/v1/auth/register          → Buat akun baru
2.  POST /api/v1/auth/login             → Dapatkan token JWT
3.  POST /api/v1/uploads                → Unggah CSV (Format mentah atau ekspor Colab)
4.  GET  /api/v1/uploads/:id            → Polling status pipeline (pending → processing → done)
5.  GET  /api/v1/products               → Dapatkan daftar produk
6.  POST /api/v1/forecasts              → Trigger peramalan Prophet atau ARIMA skala global (menggunakan upload_id)
7.  GET  /api/v1/forecasts/:id          → Polling status peramalan
8.  GET  /api/v1/forecasts/:id/details  → Ambil detail proyeksi harian beserta MAPE & RMSE
9.  GET  /api/v1/inventory/reorder      → Periksa Safety Stock dan Reorder Point produk
10. GET  /api/v1/dashboard/summary      → Ringkasan data untuk dasbor utama
```

> Semua endpoint kecuali `/auth/register` dan `/auth/login` memerlukan token `Bearer` yang dikirimkan pada header `Authorization`.

---

## Format CSV yang Didukung

Pipeline secara cerdas mendeteksi format file saat diunggah.

### Format 1 — Data Penjualan Mentah (Raw Sales Data)

| Kolom | Tipe | Wajib | Catatan |
| :--- | :--- | :--- | :--- |
| `product_name` | string | ✅ | Contoh: `"Kopi Susu"` |
| `sale_date` | YYYY-MM-DD | ✅ | |
| `quantity_sold`| integer | ✅ | |
| `revenue` | float | ❌ | |
| `category` | string | ❌ | |
| `region` | string | ❌ | |

### Format 2 — Ekspor Google Colab

Jika file mengandung struktur kolom khas Colab, backend akan memetakan kolom tersebut secara otomatis:

| Kolom Colab | Dipetakan Ke |
| :--- | :--- |
| `ds` | `sale_date` |
| `Category` | `product_name` |
| `y` / `y_capped` / `y_original` | `quantity_sold` |
| `is_holiday` / `is_payday` | Dibaca langsung, tidak perlu dihitung ulang |

*Catatan: Jika kolom `category` atau `product_name` tidak ditemukan (seperti pada berkas deret waktu global murni), backend secara otomatis mendefinisikan nama produk default sebagai `"Global"`.*

---

## Integrasi DE + ML

### Alur Pipeline

```
[Unggah CSV]
     │
     ▼
pipeline_service.py
  ├─ Deteksi format (mentah / ekspor Colab)
  ├─ Validasi kolom wajib
  ├─ enrich_features()
  │    ├─ Deteksi hari libur nasional Indonesia
  │    ├─ Tandai hari gajian (tanggal 25–31 & 1–3)
  │    └─ Batasi pencilan (IQR capping) per produk
  └─ Ingest (Upsert) → Product & SalesRecord (DB)
                              │
                              ▼
                     [POST /forecasts]
                              │
                              ▼
                   forecast_service.py
                     ├─ Query SalesRecord → DataFrame
                     ├─ _run_prophet()
                     │    ├─ add_regressor("is_holiday")
                     │    ├─ add_regressor("is_payday")
                     │    └─ Proyeksikan regressor masa depan otomatis
                     └─ _run_arima()
                          ├─ exog = [is_holiday, is_payday]
                          └─ Proyeksikan variabel eksogen masa depan otomatis
                              │
                              ▼
                   ForecastDetail (DB)
                   MAPE · RMSE · hasil prediksi harian
```

### Request Body untuk Forecast

```json
{
  "upload_id": "uuid-di-sini",
  "model": "prophet",
  "horizon_days": 30,
  "include_holidays": true
}
```
