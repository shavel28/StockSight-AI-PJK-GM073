# Laporan Detail Hasil Pengujian API & Model StockSight AI (Skala Global)

Laporan ini memuat analisis dan rincian teknis dari hasil eksekusi pengujian otomatis terhadap backend StockSight AI pada port `8001` setelah menerapkan sistem peramalan berskala global (upload-level).

---

## 📈 Rekapitulasi Tahapan Pengujian

Berikut penjelasan rinci dari ke-17 pengujian yang dilakukan:

### 1. Mengecek Health API
* **Endpoint**: `GET /health`
* **Response**: `{"status": "ok", "service": "StockSight AI API"}`
* **Penjelasan**: Memverifikasi server FastAPI berjalan dan dapat diakses.

### 2. Registrasi User Baru
* **Endpoint**: `POST /api/v1/auth/register`
* **Response**: `{"id": "f745e48b...", "name": "Test User", "email": "user_6437@example.com", "role": "user", "created_at": "..."}`
* **Penjelasan**: Berhasil mendaftarkan pengguna baru dengan email unik secara acak.

### 3. Login User
* **Endpoint**: `POST /api/v1/auth/login`
* **Response**: Mengembalikan token JWT (`access_token`).
* **Penjelasan**: Mendapatkan token JWT untuk otorisasi akses endpoint berikutnya.

### 4. GET Profile /me
* **Endpoint**: `GET /api/v1/auth/me`
* **Response**: Data profil pengguna yang terautentikasi.

### 5. Upload CSV (sample_sales.csv)
* **Endpoint**: `POST /api/v1/uploads`
* **Response**: `{"id": "70ab8487-bfc3-4471-8a82-12e3b0160a29", "status": "pending"}`
* **Penjelasan**: File sales global diunggah untuk diproses secara asinkron.

### 6. Polling Status Pemrosesan CSV
* **Endpoint**: `GET /api/v1/uploads/{upload_id}`
* **Response**: `status: done` pada siklus ke-2.
* **Penjelasan**: Seluruh baris transaksi sukses di-ingest ke database dan dikelompokkan.

### 7. Mengambil Daftar Produk
* **Endpoint**: `GET /api/v1/products`
* **Response**: Ditemukan 3 produk (Furniture, Office Supplies, Technology) dengan data penjualan yang teragregasi.

### 8. Mengambil Histori Penjualan Produk
* **Endpoint**: `GET /api/v1/products/{product_id}/sales`
* **Response**: Menemukan 877 baris transaksi penjualan untuk produk pertama (Furniture).

### 9. Update Stok Produk (Patch Stock)
* **Endpoint**: `PATCH /api/v1/products/{product_id}/stock`
* **Payload**: `{"current_stock": 50}`
* **Response**: Stok Furniture diperbarui menjadi 50 unit.

### 10. Trigger Forecasting (Prophet - Skala Global)
* **Endpoint**: `POST /api/v1/forecasts`
* **Payload (Baru)**: 
  ```json
  {
    "upload_id": "70ab8487-bfc3-4471-8a82-12e3b0160a29",
    "model": "prophet",
    "horizon_days": 30,
    "include_holidays": true
  }
  ```
* **Response**: `{"id": "74842ad9-a967-4e68-a10e-51bc5c03b05f", "status": "pending"}`
* **Penjelasan**: Mengambil identitas berkas unggahan (`upload_id`) untuk memprediksi total penjualan keseluruhan (skala global) alih-alih per produk.

### 11. Polling Status Forecasting
* **Endpoint**: `GET /api/v1/forecasts/{forecast_id}`
* **Response**: `status: done` pada siklus ke-2.
* **Penjelasan**: Prediksi selesai dijalankan menggunakan data teragregasi global.

### 12. Mengambil Hasil Detail Forecast (Validasi Data Masa Depan)
* **Endpoint**: `GET /api/v1/forecasts/{forecast_id}/details`
* **Hasil Evaluasi**:
  * **MAPE**: `921.2778%`
  * **RMSE**: `1969.893`
* **Detail Prediksi (5 hari pertama)**:
  * 2018-12-31: Qty `2191.74`
  * 2019-01-01: Qty `2565.32`
  * 2019-01-02: Qty `2134.91`
  * 2019-01-03: Qty `1320.28`
  * 2019-01-04: Qty `1303.9`
* **Penjelasan**: Nilai MAPE turun signifikan dari sebelumnya (`1778.0384%` ke `921.2778%`) karena data sales kini diakumulasikan secara global di seluruh produk, sehingga selaras dengan skala model Prophet pra-latih. Tanggal masa depan dimulai langsung pada hari berikutnya dari tanggal maksimal data sales (`2018-12-30`).

### 13. Mengambil Reorder Point & Safety Stock
* **Endpoint**: `GET /api/v1/inventory/reorder`
* **Penjelasan**: ROP dan Safety Stock tetap dihitung secara spesifik per produk (Furniture ROP: `8510.04`, Safety Stock: `3233.56`). Ini karena manajemen stok fisik selalu berada di tingkat produk individual, meskipun peramalan permintaan dilakukan pada tingkat global.

### 14. Mengambil Ringkasan Dashboard
* **Endpoint**: `GET /api/v1/dashboard/summary`
* **Response**: `{"total_products": 3, "active_alerts": 1, "uploads_count": 1, "avg_mape": 921.28}`
* **Penjelasan**: Rata-rata MAPE pada ringkasan dashboard diperbarui dengan benar menggunakan relasi join langsung ke tabel `Upload` (mengabaikan `product_id` yang bernilai null).

### 15. Mengambil Top Products
* **Endpoint**: `GET /api/v1/dashboard/top-products`
* **Response**: Menampilkan produk terlaris di seluruh unggahan.

### 16. Mengambil Informasi Model Prophet Pra-latih
* **Endpoint**: `GET /api/v1/forecasts/model/info`

### 17. Memuat Ulang Model Prophet Pra-latih
* **Endpoint**: `POST /api/v1/forecasts/model/reload`
