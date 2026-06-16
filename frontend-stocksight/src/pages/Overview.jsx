import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';

const Overview = ({ chartOptions, token, setActiveTab }) => {
  const [salesData, setSalesData] = useState({});
  const [inventoryChartData, setInventoryChartData] = useState({});
  const [dashboardSummary, setDashboardSummary] = useState({ total_sales: 0, total_products: 0, ai_accuracy: null });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchOverviewData = async () => {
      try {
        setIsLoading(true);

        const sumResponse = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/dashboard/summary', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (sumResponse.ok) {
          const sumData = await sumResponse.json();
          setDashboardSummary({
            total_sales: sumData.total_sales,
            total_products: sumData.total_products,
            ai_accuracy: sumData.ai_accuracy 
          });
        }

        const topProdResponse = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/dashboard/top-products', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (topProdResponse.ok) {
            const topProdData = await topProdResponse.json();

            const aggregatedData = topProdData.reduce((acc, item) => {
              if (!acc[item.product_name]) {
                acc[item.product_name] = { ...item }; 
              } else {
                acc[item.product_name].total_sold += item.total_sold; 
              }
              return acc;
            }, {});

            const uniqueTop = Object.values(aggregatedData);

            setSalesData({
              labels: uniqueTop.map(item => item.product_name),
              datasets: [{ 
                label: 'Total Terjual (Kuantitas)', 
                data: uniqueTop.map(item => item.total_sold),
                borderColor: '#2563EB', 
                backgroundColor: 'rgba(37, 99, 235, 0.1)', 
                borderWidth: 3, tension: 0.4, fill: true, pointBackgroundColor: '#2563EB' 
              }
            ],
          });
        }

        const invResponse = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/inventory/reorder', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (invResponse.ok) {
          const invData = await invResponse.json();

          const uniqueInv = [];
          const seenInv = new Set();
          for (const item of invData) {
            if (!seenInv.has(item.product_name)) {
              seenInv.add(item.product_name);
              uniqueInv.push(item);
            }
          }

          setInventoryChartData({
            labels: uniqueInv.map(i => i.product_name).slice(0, 5), 
            datasets: [
              { label: 'Safety Stock', data: uniqueInv.map(i => i.safety_stock).slice(0, 5), backgroundColor: '#06B6D4', borderRadius: 6 },
              { label: 'Reorder Point', data: uniqueInv.map(i => i.reorder_point).slice(0, 5), backgroundColor: '#2563EB', borderRadius: 6 }
            ],
          });
        }

      } catch (error) {
        console.error("Gagal menarik data Overview:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOverviewData();
  }, [token]);

  if (isLoading) return <div className="loader">Menghubungkan ke Backend FastAPI...</div>;

  return (
    <>
      <section className="hero-section">
        <div className="hero-image-container">
          <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1600&q=80" alt="Data Analytics" className="hero-image" />
          <div className="hero-overlay"></div>
          <div className="hero-content">
            <h1>Analisis Penjualan & Inventaris</h1>
            <p>Ringkasan performa runtun waktu global, deteksi anomali,<br/>dan status inventaris harian berbasis model Machine Learning.</p>
            <button 
              className="btn-primary" 
              onClick={() => setActiveTab('prediction')}
              style={{ position: 'relative', zIndex: 10 }}
            >
              Coba Prediksi Data Baru
            </button>
          </div>
        </div>
      </section>

      <section className="kpi-section">
        <h2>Metrik <span>Utama</span></h2>
        <div className="kpi-grid">
          <div className="kpi-card">
            <p className="kpi-label">Total Item Terjual</p>
            <h3>{new Intl.NumberFormat('id-ID').format(dashboardSummary.total_sales || 0)} <span>unit</span></h3>
            <div className="kpi-trend positive">Berdasarkan Database Penjualan</div>
          </div>
          
          <div className="kpi-card">
            <p className="kpi-label">Produk Terdaftar</p>
            <h3>{dashboardSummary.total_products || 0} <span>item</span></h3>
            <div className="kpi-trend neutral">Aktif di Sistem</div>
          </div>
          
          <div className="kpi-card">
            <p className="kpi-label">Akurasi Prediksi AI</p>
            <h3 style={{ color: dashboardSummary.ai_accuracy ? 'var(--color-success)' : 'var(--text-muted)' }}>
              {dashboardSummary.ai_accuracy ? dashboardSummary.ai_accuracy : '--'} 
              <span>{dashboardSummary.ai_accuracy ? '%' : ''}</span>
            </h3>
            <div className="kpi-trend positive">Rata-rata Akurasi Evaluasi (WAPE)</div>
          </div>
          
          <div className="kpi-card">
            <p className="kpi-label">Status Pipeline</p>
            <h3 className="text-danger">Sync</h3>
            <div className="kpi-trend neutral">Terhubung ke Database</div>
          </div>
        </div>
      </section>

      <section className="charts-section">
        <div className="big-card">
          <div className="card-info full-width">
            <div className="card-header"><h3>Top Products (Total Penjualan)</h3><span className="tag-small">Sales Data</span></div>
            <p className="desc">Distribusi produk dengan jumlah penjualan tertinggi dari data historis CSV.</p>
            <div className="canvas-container large">
              {salesData.labels && <Line options={chartOptions} data={salesData} />}
            </div>
          </div>
        </div>

        <div className="big-card">
          <div className="card-info full-width">
            <div className="card-header"><h3>Batas Stok per Kategori</h3><span className="tag-small">Inventory</span></div>
            <p className="desc">Perbandingan antara Safety Stock dan Reorder Point untuk mencegah kehabisan stok.</p>
            <div className="canvas-container">
              {inventoryChartData.labels && <Bar options={chartOptions} data={inventoryChartData} />}
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default Overview;