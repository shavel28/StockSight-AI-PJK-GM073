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
**Role: Dianwan Noven Nur Fauzian**

## 🚀 Langkah-Langkah Pengembangan Model
### 1. Impor Library
Mengimpor pustaka utama untuk manipulasi data (`pandas`, `numpy`), visualisasi (`matplotlib`, `seaborn`), pemodelan (`Prophet`), dan metrik evaluasi (`sklearn.metrics`).

### 2. Memuat dan Menyiapkan Data
Data historis dimuat dari file CSV. Agar kompatibel dengan pustaka Prophet, DataFrame harus disesuaikan formatnya:
*   Kolom waktu/tanggal harus diubah namanya menjadi `ds`.
*   Kolom target prediksi (nilai yang ingin diramal) harus diubah namanya menjadi `y`.

### 3. Rekayasa Fitur (Feature Engineering)
Meskipun Prophet menangani musiman secara otomatis, ekstraksi fitur waktu eksplisit dilakukan untuk analisis eksploratif. Fitur yang diekstrak meliputi:
*   `hour`, `dayofweek`, `quarter`, `month`, `year`
*   `weekday` dan `season` (Spring, Summer, Fall, Winter)

### 4. Pemisahan Data (Train/Test Split)
Data deret waktu dibagi berdasarkan batasan tanggal kronologis (tanggal potong / *split date*):
*   **Data Latih (Training Set):** Data sebelum tanggal potong, digunakan untuk melatih model.
*   **Data Uji (Testing Set):** Data setelah tanggal potong, digunakan sebagai validasi terhadap data aktual yang disembunyikan.

### 5. Pembuatan dan Pelatihan Model
Model `Prophet` diinisialisasi dan dilatih menggunakan *Training Set*. Pada tahap ini, model mempelajari tren garis dasar serta variasi musiman (harian, mingguan, tahunan) dari data:

```python
from prophet import Prophet
model = Prophet()
model.fit(df_train_prophet)
```

### 6. Proses Prediksi (Forecasting)
Setelah dilatih, model digunakan untuk memprediksi kerangka waktu pada *Testing Set*. Prophet mengembalikan sebuah DataFrame hasil prediksi yang berisi:
*   `yhat`: Nilai ramalan (prediksi).
*   `yhat_lower` & `yhat_upper`: Batas bawah dan atas dari interval ketidakpastian/kepercayaan.

### 7. Evaluasi Model
Kinerja prediksi dievaluasi dengan membandingkan nilai ramalan (`yhat`) terhadap data aktual di *Testing Set*. Metrik yang umum digunakan dalam pipeline ini:
*   **MAPE** (Mean Absolute Percentage Error)
*   **MAE** (Mean Absolute Error)
*   **MSE** (Mean Squared Error)

## 📊 Visualisasi
Notebook ini menyertakan visualisasi bawaan yang berguna:
*   Distribusi nilai per hari atau per musim.
*   Plot pemisahan data antara *Train* dan *Test*.
*   Plot peramalan Prophet yang menunjukkan komponen tren dan interval kepercayaan yang memisahkan data masa lalu dengan masa depan.

---

### ⚙️ Backend Development
**Role: Arizal**
*(Silakan isi detail pengembangan sistem backend dan API di sini)*

---

### 🎨 UI/UX Design
**Role: Rania**
## 🚀 Live Demo
*   **Web Application:** [https://frontend-stocksight.vercel.app/](https://frontend-stocksight.vercel.app/)
*   **UI/UX Design:** [Figma Prototype](https://www.figma.com/proto/xirMecvPVe3EiBnoErwhIr/CAPSTONE?node-id=137-905&p=f&t=flw4VGgZq187hqIF-1&scaling=min-zoom&content-scaling=fixed&page-id=0%3A1&starting-point-node-id=137%3A905)


## 🛠 Role & Kontribusi
Sebagai **Frontend Developer & UI/UX Designer**, tanggung jawab utama meliputi:
*   **UI/UX Design:** Merancang antarmuka pengguna yang bersih, responsif, dan intuitif dengan fokus pada kemudahan navigasi bagi analis data.
*   **Frontend Development:** Mengimplementasikan desain ke dalam *React.js* dengan dukungan *Tailwind CSS* untuk styling dan *Chart.js* untuk visualisasi data yang kompleks.
*   **Data Visualization:** Membangun dashboard interaktif yang mampu menerjemahkan output model AI ke dalam bentuk grafik agar mudah dipahami oleh pengguna non-teknis.


## 📋 Fitur Dashboard (Navigasi)

1.  **Overview:** Ringkasan KPI performa (rata-rata permintaan, deteksi anomali), visualisasi *Forecasting* AI, dan perbandingan batas stok.
2.  **Inventory:** Manajemen inventaris real-time, menampilkan status stok (Aman/Rendah/Kritis) berdasarkan rekomendasi AI.
3.  **Data Pipeline:** Pemantauan proses *preprocessing* data, log transformasi, dan integrasi dataset eksternal.
4.  **Prediksi Baru:** Simulasi prediksi interaktif dengan opsi pemilihan model (Prophet/ARIMA/LSTM) dan pengaturan horizon waktu.
5.  **Config AI:** Pengaturan *tuning* parameter model AI untuk menyesuaikan sensitivitas tren data.


## 💻 Tech Stack & Dokumentasi Teknis
Proyek ini dibangun menggunakan **React** dan **Vite** untuk pengalaman pengembangan yang cepat dan efisien.

*   **Framework:** React.js (Vite)
*   **Styling:** Tailwind CSS
*   **Charts:** Chart.js & react-chartjs-2
*   **Deployment:** Vercel

### Informasi Teknis:
*   **Build Tool:** Template ini menggunakan `@vitejs/plugin-react` yang memanfaatkan *Oxc* untuk kompilasi yang lebih cepat.
*   **React Compiler:** Saat ini tidak diaktifkan untuk menjaga performa *build* dan *dev*. Jika dibutuhkan optimasi lebih lanjut di masa depan, dapat diaktifkan melalui panduan resmi React.
*   **Rekomendasi:** Untuk pengembangan skala besar, disarankan menggunakan *TypeScript* dengan `typescript-eslint` untuk menjaga kualitas kode dan keamanan tipe data.


## ⚙️ Cara Menjalankan Lokal
1. Clone repositori:
   `git clone https://github.com/aryuzura/stocksight-frontend.git`
2. Install dependencies:
   `npm install`
3. Jalankan server pengembangan:
   `npm run dev`

---

### 📋 Product Management
**Role: Tengku Farkhan A.S**
*(Silakan isi detail perencanaan dan cakupan proyek di sini)*
