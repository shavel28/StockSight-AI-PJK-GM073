# 🥬 StockSight AI - PJK-GM073
**AI-Powered Demand Forecasting & Inventory Dashboard for UMKM**

StockSight AI adalah solusi cerdas untuk membantu UMKM mengelola stok barang secara otomatis menggunakan kecerdasan buatan.

---

## 👥 Kontribusi Anggota Tim

### 📂 Data Engineering
**Role: Shava Selvia R.S**

Sebagai Data Engineer, saya membangun *end-to-end data pipeline* dari sumber mentah hingga menjadi metrik bisnis yang tervalidasi. Berikut adalah detail teknis pengerjaan saya:

#### 1. Data Ingestion & Preprocessing
- **Source**: Mengambil dataset "Sales Forecasting" dari Kaggle (`rohitsahoo/sales-forecasting`) menggunakan library `kagglehub`.
- **Cleaning**: Melakukan pembersihan otomatis terhadap data duplikat dan baris kosong (*missing values*) pada kolom krusial (Sales & Order Date).
- **Date Validation**: Memastikan format tanggal konsisten dan mengurutkan data secara kronologis untuk kebutuhan analisis *Time Series*.

#### 2. Feature Engineering (Holiday Integration)
- Mengintegrasikan library `holidays` untuk menyuntikkan data **Hari Libur Nasional Indonesia**.
- **Rentang Waktu**: Menyiapkan kalender libur dari tahun **2015 hingga 2025** untuk memastikan semua data historis dan rencana masa depan ter-cover.
- **Output Fitur**: Menghasilkan fitur biner `is_holiday` (1 untuk libur, 0 untuk hari biasa) yang berfungsi sebagai pengukur lonjakan permintaan (*demand spikes*).

#### 3. Data Transformation (ML-Ready)
- Melakukan agregasi total penjualan harian.
- Mengubah struktur data ke format standar library Prophet:
  - `ds`: Kolom tanggal bersih.
  - `y`: Nilai total penjualan (Sales).
  - `is_holiday`: Penanda hari libur nasional.

#### 4. Inventory Analytics (Business Logic)
Menghitung metrik penting untuk operasional gudang dengan asumsi *Lead Time* (waktu pengiriman) selama **7 hari**:
- **Safety Stock**: Dihitung menggunakan selisih penjualan maksimal dan rata-rata untuk menghindari *stockout*.
  - *Rumus: (Max Sales * Lead Time) - (Avg Sales * Lead Time)*
- **Reorder Point (ROP)**: Titik pemesanan ulang otomatis.
  - *Rumus: (Avg Sales * Lead Time) + Safety Stock*

#### 5. Output & Quality Control
- Menghasilkan file `processed_sales.csv` untuk digunakan oleh **(ML Engineer)**.
- Menghasilkan file `inventory_summary.csv` berisi angka ROP untuk **(Backend Developer)**.
- Menyertakan visualisasi tren penjualan harian dan deteksi *outlier* untuk menjamin kualitas data sebelum tahap pemodelan.

---

### 🤖 Machine Learning
**Role: Dianwan**
*(Silakan isi detail proses pengembangan model di sini)*

---

### ⚙️ Backend Development
**Role: Arizal**
*(Silakan isi detail pengembangan sistem backend dan API di sini)*

---

### 🎨 UI/UX Design
**Role: Rania**
*(Silakan isi detail desain interface dashboard di sini)*

---

### 📋 Product Management
**Role: Tengku Farkhan A.S**
*(Silakan isi detail perencanaan dan cakupan proyek di sini)*
