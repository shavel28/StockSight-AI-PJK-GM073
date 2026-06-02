# 🥬 StockSight AI - PJK-GM073
**AI-Powered Demand Forecasting & Inventory Dashboard for UMKM**

StockSight AI adalah solusi cerdas untuk membantu UMKM mengelola stok barang secara otomatis menggunakan kecerdasan buatan.

---

## 👥 Kontribusi Anggota Tim

### 📂 Data Engineering

**Role: Shava Selvia Ramadhani Subekti**

Sebagai Data Engineer, saya membangun *end-to-end data pipeline* yang mengubah data mentah menjadi dataset siap pakai (*ML-ready dataset*) untuk kebutuhan forecasting permintaan dan analisis inventori pada sistem StockSight AI.

#### 1. Data Ingestion & Validation

* Mengambil dataset **Sales Forecasting** dari Kaggle menggunakan library `kagglehub`.
* Melakukan validasi struktur data dan pemeriksaan kualitas data sebelum proses analisis.
* Memastikan kolom penting seperti *Order Date*, *Sales*, dan *Category* dapat digunakan pada proses forecasting.

#### 2. Data Cleaning & Preprocessing

* Menghapus data duplikat (*duplicate records*).
* Menangani data kosong (*missing values*) pada atribut penting.
* Melakukan validasi format tanggal (*date validation*) dan konversi ke format *datetime*.
* Memastikan data penjualan (*Sales*) valid dan dapat digunakan untuk analisis lebih lanjut.

#### 3. Holiday Integration

* Mengintegrasikan dataset eksternal menggunakan library `holidays`.
* Menambahkan fitur **Hari Libur Nasional Indonesia** sebagai variabel eksternal.
* Menghasilkan fitur biner `is_holiday`:

  * `1` = Hari Libur Nasional
  * `0` = Hari Biasa
* Fitur ini digunakan untuk membantu model mengenali pola lonjakan permintaan pada periode tertentu.

#### 4. Time Series Transformation

* Mengubah data transaksi menjadi format *time series* untuk kebutuhan forecasting.
* Membuat dataset:

  * **Time Series Global** (total penjualan harian).
  * **Time Series per Product Category**.
* Menyesuaikan struktur data agar kompatibel dengan model forecasting seperti Prophet:

  * `ds` : tanggal
  * `y` : nilai penjualan
  * `is_holiday` : indikator hari libur

#### 5. Feature Engineering

Untuk meningkatkan kualitas data yang digunakan model forecasting, dilakukan beberapa proses *feature engineering*:

* **Calendar Features**

  * Day of Week
  * Month
  * Quarter
  * Year
  * Weekend Indicator

* **Lag Features**

  * Lag 1 Day
  * Lag 7 Days
  * Lag 14 Days

* **Rolling Statistics**

  * Rolling Mean 7 Hari
  * Rolling Mean 30 Hari

* **Missing Date Handling**

  * Melengkapi tanggal yang hilang pada data time series agar data bersifat kontinu.

#### 6. Outlier Analysis & Quality Control

* Melakukan analisis outlier menggunakan metode **Interquartile Range (IQR)**.
* Menghasilkan ringkasan jumlah outlier pada setiap kategori produk.
* Menyediakan visualisasi tren penjualan untuk membantu proses validasi kualitas data sebelum pemodelan.

#### 7. Inventory Analytics

Melakukan perhitungan metrik inventori untuk mendukung pengambilan keputusan stok barang dengan asumsi **Lead Time = 7 hari**.

##### Safety Stock

Menghitung stok pengaman untuk mengurangi risiko kehabisan stok (*stockout*) akibat fluktuasi permintaan.

Formula:

Safety Stock = Z × Standard Deviation Demand × √Lead Time

##### Reorder Point (ROP)

Menentukan titik pemesanan ulang agar persediaan tetap tersedia saat proses pengiriman berlangsung.

Formula:

ROP = (Average Daily Demand × Lead Time) + Safety Stock

Perhitungan dilakukan untuk setiap kategori produk sehingga rekomendasi inventori menjadi lebih akurat.

#### 8. Output Dataset

Menghasilkan beberapa dataset hasil preprocessing yang digunakan pada tahapan selanjutnya:

* `time_series_global.csv`
* `time_series_category_feature_engineered.csv`
* `outlier_summary.csv`
* `inventory_summary.csv`

Dataset tersebut digunakan sebagai input bagi **Machine Learning Engineer** untuk proses pelatihan dan evaluasi model forecasting.

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
