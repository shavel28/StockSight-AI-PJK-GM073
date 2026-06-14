import httpx
import time
import sys
import os
import random

BASE_URL = "http://localhost:8001"

def test_api():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    print("=== 1. Mengecek Health API ===")
    try:
        r = client.get("/health")
        print(f"Status: {r.status_code}, Response: {r.json()}")
    except Exception as e:
        print(f"Error: Tidak dapat menghubungi API di {BASE_URL}. Pastikan uvicorn sudah berjalan!")
        sys.exit(1)
        
    print("\n=== 2. Registrasi User Baru ===")
    # Gunakan email acak agar tidak bentrok jika dijalankan berulang kali
    test_email = f"user_{random.randint(1000, 9999)}@example.com"
    register_payload = {
        "name": "Test User",
        "email": test_email,
        "password": "securepassword123"
    }
    r = client.post("/api/v1/auth/register", json=register_payload)
    if r.status_code == 201:
        print(f"Registrasi Sukses: {r.json()}")
    else:
        print(f"Registrasi Gagal: {r.status_code} - {r.text}")
        sys.exit(1)
        
    print("\n=== 3. Login User ===")
    login_payload = {
        "email": test_email,
        "password": "securepassword123"
    }
    r = client.post("/api/v1/auth/login", json=login_payload)
    if r.status_code == 200:
        token_data = r.json()
        token = token_data["access_token"]
        print("Login Sukses, Token berhasil diperoleh.")
    else:
        print(f"Login Gagal: {r.status_code} - {r.text}")
        sys.exit(1)
        
    # Set Authorization Header untuk request selanjutnya
    headers = {"Authorization": f"Bearer {token}"}
    client.headers.update(headers)
    
    print("\n=== 4. GET Profile /me ===")
    r = client.get("/api/v1/auth/me")
    print(f"Profile: {r.json()}")
    
    print("\n=== 5. Upload CSV (sample_sales.csv) ===")
    csv_file = "sample_sales.csv"
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} tidak ditemukan. Silakan jalankan generate_sample_csv.py terlebih dahulu!")
        sys.exit(1)
        
    with open(csv_file, "rb") as f:
        files = {"file": (csv_file, f, "text/csv")}
        r = client.post("/api/v1/uploads", files=files)
        
    if r.status_code == 202:
        upload_data = r.json()
        upload_id = upload_data["id"]
        print(f"Upload sukses! ID: {upload_id}, Status: {upload_data['status']}")
    else:
        print(f"Upload gagal: {r.status_code} - {r.text}")
        sys.exit(1)
        
    print("\n=== 6. Polling Status Pemrosesan CSV ===")
    max_retries = 10
    for i in range(max_retries):
        r = client.get(f"/api/v1/uploads/{upload_id}")
        status = r.json().get("status")
        print(f"Mengecek status upload... (Siklus {i+1}): {status}")
        if status == "done":
            print("CSV selesai diproses oleh pipeline!")
            break
        elif status == "error":
            print(f"Error pada pipeline: {r.json().get('error_message')}")
            sys.exit(1)
        time.sleep(1)
    else:
        print("Polling timeout: Pemrosesan CSV memakan waktu terlalu lama.")
        sys.exit(1)
        
    print("\n=== 7. Mengambil Daftar Produk ===")
    r = client.get("/api/v1/products")
    products = r.json()
    print(f"Ditemukan {len(products)} produk.")
    for idx, prod in enumerate(products):
        print(f"  {idx+1}. ID: {prod['id']}, Nama: {prod['product_name']}, Kategori: {prod['category']}")
        
    if not products:
        print("Error: Tidak ada produk yang ter-ingest.")
        sys.exit(1)
        
    target_product_id = products[0]["id"]
    target_product_name = products[0]["product_name"]
    print(f"\nMenggunakan produk pertama: '{target_product_name}' (ID: {target_product_id}) untuk pengujian selanjutnya.")
    
    print("\n=== 8. Mengambil Histori Penjualan Produk ===")
    r = client.get(f"/api/v1/products/{target_product_id}/sales")
    sales = r.json()
    print(f"Ditemukan {len(sales)} baris histori penjualan untuk produk ini.")
    
    print("\n=== 9. Update Stok Produk (Patch Stock) ===")
    r = client.patch(f"/api/v1/products/{target_product_id}/stock", json={"current_stock": 50})
    if r.status_code == 200:
        print(f"Update stok sukses! Stok saat ini: {r.json()['current_stock']}")
    else:
        print(f"Update stok gagal: {r.status_code} - {r.text}")
        
    print("\n=== 10. Trigger Forecasting (Prophet) ===")
    forecast_payload = {
        "upload_id": upload_id,
        "model": "prophet",
        "horizon_days": 30,
        "include_holidays": True
    }
    r = client.post("/api/v1/forecasts", json=forecast_payload)
    if r.status_code == 202:
        forecast_data = r.json()
        forecast_id = forecast_data["id"]
        print(f"Trigger forecast sukses! ID: {forecast_id}, Status: {forecast_data['status']}")
    else:
        print(f"Trigger forecast gagal: {r.status_code} - {r.text}")
        sys.exit(1)
        
    print("\n=== 11. Polling Status Forecasting ===")
    for i in range(20):
        r = client.get(f"/api/v1/forecasts/{forecast_id}")
        status = r.json().get("status")
        print(f"Mengecek status forecast... (Siklus {i+1}): {status}")
        if status == "done":
            print("Forecasting selesai dijalankan!")
            break
        elif status == "error":
            print("Forecasting gagal diselesaikan (cek server log).")
            sys.exit(1)
        time.sleep(2)
    else:
        print("Polling timeout: Forecasting memakan waktu terlalu lama.")
        sys.exit(1)
        
    print("\n=== 12. Mengambil Hasil Detail Forecast ===")
    r = client.get(f"/api/v1/forecasts/{forecast_id}/details")
    if r.status_code == 200:
        details_data = r.json()
        print(f"MAPE: {details_data.get('mape')}%")
        print(f"RMSE: {details_data.get('rmse')}")
        print(f"Menampilkan 5 hari pertama prediksi:")
        for day in details_data.get("details", [])[:5]:
            print(f"  Tanggal: {day['forecast_date']}, Qty Prediksi: {day['predicted_qty']}, Batas Bawah: {day['lower_bound']}, Batas Atas: {day['upper_bound']}")
    else:
        print(f"Gagal mengambil detail: {r.status_code} - {r.text}")
        
    print("\n=== 13. Mengambil Reorder Point & Safety Stock ===")
    r = client.get("/api/v1/inventory/reorder")
    if r.status_code == 200:
        reorders = r.json()
        for ro in reorders:
            print(f"Product: {ro['product_name']}, Stok Saat Ini: {ro['current_stock']}, ROP: {ro['reorder_point']}, Safety Stock: {ro['safety_stock']}, Butuh Reorder: {ro['needs_reorder']}")
    else:
        print(f"Gagal mengambil data ROP: {r.status_code} - {r.text}")
        
    print("\n=== 14. Mengambil Ringkasan Dashboard ===")
    r = client.get("/api/v1/dashboard/summary")
    if r.status_code == 200:
        print(f"Ringkasan Dashboard: {r.json()}")
    else:
        print(f"Gagal mengambil ringkasan dashboard: {r.status_code} - {r.text}")
        
    print("\n=== 15. Mengambil Top Products ===")
    r = client.get("/api/v1/dashboard/top-products")
    if r.status_code == 200:
        print("Top Products berdasarkan penjualan:")
        for idx, tp in enumerate(r.json()):
            print(f"  {idx+1}. {tp['product_name']} ({tp['category']}) - Total Terjual: {tp['total_sold']}")
    else:
        print(f"Gagal mengambil top products: {r.status_code} - {r.text}")

    print("\n=== 16. Mengambil Informasi Model Prophet Pra-latih ===")
    r = client.get("/api/v1/forecasts/model/info")
    if r.status_code == 200:
        print(f"Informasi Model: {r.json()}")
    else:
        print(f"Gagal mengambil info model: {r.status_code} - {r.text}")
        sys.exit(1)

    print("\n=== 17. Memuat Ulang Model Prophet Pra-latih ===")
    r = client.post("/api/v1/forecasts/model/reload")
    if r.status_code == 200:
        print(f"Hasil Reload Model: {r.json()}")
    else:
        print(f"Gagal reload model: {r.status_code} - {r.text}")
        sys.exit(1)

    print("\n=============================================")
    print(" SELURUH PENGUJIAN ENDPOINT SELESAI & BERHASIL!")
    print("=============================================")

if __name__ == "__main__":
    test_api()
