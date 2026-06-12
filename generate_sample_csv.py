import pandas as pd
from datetime import datetime, timedelta

def generate_sample_csv():
    # Buat data dummy untuk 2 produk selama 15 hari terakhir
    base_date = datetime.now() - timedelta(days=15)
    
    data = []
    products = [
        {"name": "Kopi Susu Gula Aren", "category": "Minuman", "region": "Jakarta", "avg_qty": 25, "revenue_per_item": 15000},
        {"name": "Roti Bakar Cokelat", "category": "Makanan", "region": "Jakarta", "avg_qty": 12, "revenue_per_item": 20000}
    ]
    
    for i in range(15):
        sale_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for prod in products:
            # Variasikan kuantitas penjualan secara acak
            import random
            random.seed(i + hash(prod["name"]))  # Reproducible random data
            qty = max(5, prod["avg_qty"] + random.randint(-5, 5))
            revenue = qty * prod["revenue_per_item"]
            
            data.append({
                "product_name": prod["name"],
                "sale_date": sale_date,
                "quantity_sold": qty,
                "revenue": revenue,
                "category": prod["category"],
                "region": prod["region"]
            })
            
    df = pd.DataFrame(data)
    filename = "sample_sales.csv"
    df.to_csv(filename, index=False)
    print(f"File {filename} berhasil dibuat dengan {len(df)} baris data!")

if __name__ == "__main__":
    generate_sample_csv()
