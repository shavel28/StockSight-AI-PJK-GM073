# 🥬 StockSight AI - PJK-GM073
**AI-Powered Demand Forecasting & Inventory Dashboard for UMKM**

StockSight AI adalah solusi cerdas untuk membantu UMKM mengelola stok barang secara otomatis menggunakan kecerdasan buatan.

---

## 👥 Kontribusi Anggota Tim

### 📂 Data Engineering

**Role: Shava Selvia Ramadhani Subekti**

Sebagai Data Engineer, saya bertanggung jawab membangun *end-to-end data pipeline* mulai dari proses pengambilan data mentah, pembersihan data, integrasi data eksternal, transformasi data menjadi format *time series*, hingga menghasilkan dataset siap pakai (*ML-ready dataset*) untuk proses forecasting dan analisis inventori pada sistem StockSight AI.

#### 📊 Dataset Source

Dataset utama yang digunakan berasal dari Kaggle:

* **Dataset Name:** Sales Forecasting Dataset
* **Author:** Rohit Sahoo
* **Source:** https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting

> **Note:**
> Dataset utama berasal dari Kaggle, sedangkan fitur hari libur diperoleh dari library `holidays` dengan kalender Hari Libur Nasional Indonesia sebagai variabel eksternal untuk mendukung forecasting.

---

#### 1. Data Ingestion & Validation

* Mengambil dataset dari Kaggle menggunakan library `kagglehub`.
* Melakukan pemeriksaan struktur data dan validasi atribut penting.
* Memastikan kolom seperti *Order Date*, *Sales*, dan *Category* dapat digunakan pada proses analisis dan forecasting.

#### 2. Data Cleaning & Preprocessing

* Menghapus data duplikat (*duplicate records*).
* Menangani data kosong (*missing values*) pada atribut penting.
* Melakukan validasi format tanggal (*date validation*).
* Mengonversi kolom tanggal ke format *datetime*.
* Memastikan nilai penjualan (*Sales*) valid dan siap digunakan untuk analisis.

#### 3. Holiday Integration

* Mengintegrasikan data Hari Libur Nasional Indonesia menggunakan library `holidays`.
* Menambahkan fitur biner `is_holiday`:

  * `1` = Hari Libur Nasional
  * `0` = Hari Biasa
* Fitur ini digunakan untuk membantu model mengenali pola perubahan permintaan yang dipengaruhi oleh hari libur nasional.

#### 4. Time Series Transformation

Melakukan transformasi data transaksi menjadi format *time series* yang siap digunakan untuk model forecasting.

Dataset yang dihasilkan:

* **Time Series Global** (total penjualan harian)
* **Time Series per Product Category**

Struktur data yang digunakan:

* `ds` → Tanggal transaksi
* `y` → Nilai penjualan
* `is_holiday` → Indikator hari libur

#### 5. Feature Engineering

Untuk meningkatkan kualitas data yang digunakan model forecasting, dilakukan beberapa proses *feature engineering*:

##### Calendar Features

* Day of Week
* Month
* Quarter
* Year
* Weekend Indicator

##### Lag Features

* Lag 1 Day
* Lag 7 Days
* Lag 14 Days

##### Rolling Statistics

* Rolling Mean 7 Hari
* Rolling Mean 30 Hari

##### Missing Date Handling

* Melengkapi tanggal yang hilang agar data *time series* bersifat kontinu dan konsisten.

#### 6. Outlier Analysis & Quality Control

* Melakukan analisis outlier menggunakan metode **Interquartile Range (IQR)**.
* Mengidentifikasi data penjualan yang berada di luar batas normal.
* Menghasilkan ringkasan jumlah outlier pada setiap kategori produk.
* Menyediakan visualisasi tren penjualan untuk membantu proses validasi kualitas data sebelum digunakan oleh model machine learning.

#### 7. Inventory Analytics

Melakukan analisis inventori untuk mendukung pengambilan keputusan pengelolaan stok barang.

##### Safety Stock

Menghitung stok pengaman (*Safety Stock*) untuk mengurangi risiko kehabisan stok akibat fluktuasi permintaan.

**Formula:**

Safety Stock = Z × Standard Deviation Demand × √Lead Time

##### Reorder Point (ROP)

Menentukan titik pemesanan ulang (*Reorder Point*) agar stok tetap tersedia selama proses pengiriman berlangsung.

**Formula:**

ROP = (Average Daily Demand × Lead Time) + Safety Stock

Perhitungan dilakukan untuk setiap kategori produk sehingga rekomendasi inventori menjadi lebih akurat dan relevan.

#### 8. Output Dataset

Sebagai hasil akhir proses Data Engineering, dihasilkan beberapa dataset yang digunakan oleh Machine Learning Engineer untuk proses pelatihan dan evaluasi model:

* `time_series_global.csv`
* `time_series_category_feature_engineered.csv`
* `outlier_summary.csv`
* `inventory_summary.csv`

Seluruh dataset telah melalui proses validasi, preprocessing, feature engineering, dan quality control sehingga siap digunakan pada tahap forecasting dan analisis inventori.

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
