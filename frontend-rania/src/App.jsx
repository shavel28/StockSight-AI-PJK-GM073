import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const App = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [salesData, setSalesData] = useState({});
  const [inventoryChartData, setInventoryChartData] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);

  const [inventoryList] = useState([
    { id: 'CAT-FUR', category: 'Furniture', avgDemand: 499.77, safetyStock: 3847.73, reorderPoint: 7346.09, currentStock: 8500, status: 'Aman' },
    { id: 'CAT-OFF', category: 'Office Supplies', avgDemand: 483.83, safetyStock: 3978.26, reorderPoint: 7365.06, currentStock: 5000, status: 'Stok Rendah' },
    { id: 'CAT-TEC', category: 'Technology', avgDemand: 567.53, safetyStock: 6296.08, reorderPoint: 10268.78, currentStock: 4200, status: 'Kritis' },
  ]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const timeSeriesData = {
          dates: ['1 Nov', '2 Nov', '3 Nov', '4 Nov', '5 Nov', '6 Nov', '7 Nov'],
          actualSales: [2921.43, 6294.38, 4536.93, 10668.09, 2355.06, 4288.75, 2413.37],
          predictedSales: [2850.00, 6100.00, 4800.00, 10200.00, 2500.00, 4100.00, 2600.00],
        };

        setSalesData({
          labels: timeSeriesData.dates,
          datasets: [
            {
              label: 'Penjualan Aktual',
              data: timeSeriesData.actualSales,
              borderColor: '#2563EB',
              backgroundColor: 'rgba(37, 99, 235, 0.1)',
              borderWidth: 3,
              tension: 0.4,
              fill: true,
              pointBackgroundColor: '#2563EB',
            },
            {
              label: 'Prediksi AI (Prophet)',
              data: timeSeriesData.predictedSales,
              borderColor: '#06B6D4',
              borderWidth: 2,
              borderDash: [5, 5],
              tension: 0.4,
              pointRadius: 0,
            },
          ],
        });

        setInventoryChartData({
          labels: ['Furniture', 'Office Supplies', 'Technology'],
          datasets: [
            {
              label: 'Safety Stock',
              data: [3847.73, 3978.26, 6296.08],
              backgroundColor: '#06B6D4',
              borderRadius: 6,
            },
            {
              label: 'Reorder Point',
              data: [7346.09, 7365.06, 10268.78],
              backgroundColor: '#2563EB',
              borderRadius: 6,
            }
          ],
        });

        setIsLoading(false);
      } catch (error) {
        console.error("Gagal memuat data:", error);
      }
    };

    fetchDashboardData();
  }, []);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { 
        position: 'top', 
        labels: { 
          usePointStyle: true, 
          boxWidth: 8, 
          font: { family: 'News Cycle' } 
        } 
      } 
    },
    scales: {
      y: { 
        grid: { borderDash: [4, 4], color: '#E2E8F0' }, 
        ticks: { font: { family: 'News Cycle' } } 
      },
      x: { 
        grid: { display: false }, 
        ticks: { font: { family: 'News Cycle' } } 
      }
    }
  };

  const handleRunPrediction = (e) => {
    e.preventDefault();
    setIsPredicting(true);
    setPredictionResult(null);

    setTimeout(() => {
      setPredictionResult({
        labels: ['Bulan 1', 'Bulan 2', 'Bulan 3', 'Bulan 4', 'Bulan 5', 'Bulan 6'],
        datasets: [
          {
            label: 'Proyeksi Permintaan Baru',
            data: [4200, 4800, 5100, 4900, 6200, 6800],
            borderColor: '#7C3AED',
            backgroundColor: 'rgba(124, 58, 237, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
          }
        ],
        confidenceScore: '92.4%',
        estimatedAnomalies: 2,
        recommendedAction: 'Tingkatkan Safety Stock sebesar 15% pada Bulan ke-5.'
      });
      setIsPredicting(false);
    }, 2500);
  };

  return (
    <div className="page-wrapper">
      <div className="app-container">
      
        <header className="navbar">
          <div className="logo">
            <img src="/logo.png" alt="Stocksight AI" className="logo-img" />
            <span>Stocksight AI</span>
          </div>
          <nav className="nav-links">
            <button 
              className={activeTab === 'overview' ? 'active' : ''} 
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button 
              className={activeTab === 'inventory' ? 'active' : ''} 
              onClick={() => setActiveTab('inventory')}
            >
              Inventory
            </button>
            <button 
              className={activeTab === 'data-prep' ? 'active' : ''} 
              onClick={() => setActiveTab('data-prep')}
            >
              Data Pipeline
            </button>
            <button 
              className={activeTab === 'prediction' ? 'active' : ''} 
              onClick={() => setActiveTab('prediction')}
            >
              Prediksi Baru
            </button>
            <button 
              className={activeTab === 'settings' ? 'active' : ''} 
              onClick={() => setActiveTab('settings')}
            >
              Config AI
            </button>
          </nav>
          <div className="user-profile">
            <div className="avatar">PJK</div>
            <span className="user-name">PJK-GM073</span>
          </div>
        </header>

        {isLoading ? (
          <div className="loader">Memuat Data Analitik...</div>
        ) : (
          <div className="tab-content fade-in">
            {activeTab === 'overview' && (
              <>
                <section className="hero-section">
                  <div className="hero-image-container">
                    <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1600&q=80" alt="Data Analytics" className="hero-image" />
                    <div className="hero-overlay"></div>
                    <div className="hero-content">
                      <h1>Analisis Penjualan & Inventaris</h1>
                      <p>Ringkasan performa runtun waktu global, deteksi anomali,<br/>dan status inventaris harian berbasis model Machine Learning.</p>
                      <button className="btn-primary">Unduh Laporan PDF</button>
                    </div>
                  </div>
                </section>

                <section className="kpi-section">
                  <h2>Metrik <span>Utama</span></h2>
                  <div className="kpi-grid">
                    <div className="kpi-card">
                      <p className="kpi-label">Avg. Demand (Tech)</p>
                      <h3>567.53 <span>unit</span></h3>
                      <div className="kpi-trend positive">+12.5% vs last week</div>
                    </div>
                    <div className="kpi-card">
                      <p className="kpi-label">Total Anomali Terdeteksi</p>
                      <h3 className="text-danger">423 <span>outliers</span></h3>
                      <div className="kpi-trend negative">Perlu peninjauan</div>
                    </div>
                    <div className="kpi-card">
                      <p className="kpi-label">Kategori Kritis</p>
                      <h3 className="text-danger">Technology</h3>
                      <div className="kpi-trend neutral">Stok di bawah batas aman</div>
                    </div>
                    <div className="kpi-card">
                      <p className="kpi-label">Akurasi Model (Prophet)</p>
                      <h3>94.2 <span>%</span></h3>
                      <div className="kpi-trend positive">Berdasarkan MAPE</div>
                    </div>
                  </div>
                </section>

                <section className="charts-section">
                  <div className="big-card">
                    <div className="card-info full-width">
                      <div className="card-header">
                        <h3>Forecasting Global (7 Hari)</h3>
                        <span className="tag-small">Prophet AI</span>
                      </div>
                      <p className="desc">Prediksi pergerakan permintaan barang berdasarkan data historis dan tren musiman (seasonality).</p>
                      <div className="canvas-container large">
                        <Line options={chartOptions} data={salesData} />
                      </div>
                    </div>
                  </div>

                  <div className="big-card">
                    <div className="card-info full-width">
                      <div className="card-header">
                        <h3>Batas Stok per Kategori</h3>
                        <span className="tag-small">Inventory</span>
                      </div>
                      <p className="desc">Perbandingan antara Safety Stock dan Reorder Point untuk mencegah stockout.</p>
                      <div className="canvas-container">
                        <Bar options={chartOptions} data={inventoryChartData} />
                      </div>
                    </div>
                  </div>
                </section>
              </>
            )}

            {activeTab === 'inventory' && (
              <section className="table-section fade-in">
                <div className="section-header">
                  <div>
                    <h2>Manajemen <span>Inventaris</span></h2>
                    <p className="desc" style={{marginBottom: 0, marginTop: '4px'}}>Pantau metrik reorder point dan safety stock berdasarkan AI.</p>
                  </div>
                  <div className="header-actions-inline">
                    <button className="btn-secondary">Export CSV</button>
                    <button className="btn-primary">Tambah Stok Manual</button>
                  </div>
                </div>
                
                <div className="table-wrapper">
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>ID Item</th>
                        <th>Kategori</th>
                        <th>Avg. Demand</th>
                        <th>Safety Stock</th>
                        <th>Reorder Point</th>
                        <th>Current Stock</th>
                        <th>Status AI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inventoryList.map((item) => (
                        <tr key={item.id}>
                          <td><span className="id-tag">{item.id}</span></td>
                          <td><strong>{item.category}</strong></td>
                          <td>{item.avgDemand.toFixed(2)}</td>
                          <td>{item.safetyStock.toFixed(2)}</td>
                          <td>{item.reorderPoint.toFixed(2)}</td>
                          <td><strong>{item.currentStock}</strong></td>
                          <td>
                            <span className={`badge badge-${item.status.toLowerCase().replace(' ', '-')}`}>
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
            {activeTab === 'data-prep' && (
              <section className="prediction-section fade-in">
                <div className="section-header">
                  <div>
                    <h2>Preprocessing & <span>Integrasi Data</span></h2>
                    <p className="desc" style={{marginBottom: 0, marginTop: '4px'}}>Validasi, pembersihan data, dan integrasi dataset eksternal (Holiday) untuk akurasi model.</p>
                  </div>
                  <div className="header-actions-inline">
                    <button className="btn-secondary">Lihat Log Transformasi</button>
                    <button className="btn-primary">Jalankan Ulang Pipeline</button>
                  </div>
                </div>

                <div className="charts-section" style={{ gridTemplateColumns: '1fr 1fr' }}>
                  <div className="big-card">
                    <div className="card-header" style={{ marginBottom: '24px' }}>
                      <h3>Pembersihan Data Penjualan</h3>
                      <span className="tag-small success-tag">Ready</span>
                    </div>
                    <div className="kpi-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                      <div className="kpi-card" style={{ padding: '20px', margin: 0, boxShadow: 'none' }}>
                        <p className="kpi-label">Missing Values Ditangani</p>
                        <h3 style={{ fontSize: '1.8rem', color: 'var(--primary)' }}>1,245</h3>
                        <p className="help-text">Metode: Interpolasi Time Series</p>
                      </div>
                      <div className="kpi-card" style={{ padding: '20px', margin: 0, boxShadow: 'none' }}>
                        <p className="kpi-label">Duplikasi Dihapus</p>
                        <h3 style={{ fontSize: '1.8rem', color: 'var(--primary)' }}>87</h3>
                        <p className="help-text">Duplikasi direcord dihapus</p>
                      </div>
                    </div>
                    <p className="desc">Data historis telah dibersihkan dan diformat menjadi struktur <i>Time Series</i> siap pakai untuk injeksi ke model Prophet/ARIMA.</p>
                  </div>

                  <div className="big-card">
                    <div className="card-header" style={{ marginBottom: '24px' }}>
                      <h3>Integrasi Dataset Eksternal</h3>
                      <span className="tag-small" style={{ borderColor: 'var(--color-warning)', color: 'var(--color-warning)' }}>Active API</span>
                    </div>
                    
                    <div className="result-insight-box" style={{ margin: '0 0 24px 0', borderLeftColor: 'var(--primary)' }}>
                      <p><strong>Dataset Hari Libur (Holiday Effect)</strong></p>
                      <p className="help-text">Integrasi API Kalender Nasional Indonesia. Membantu model mengantisipasi lonjakan permintaan (spike) saat tanggal merah atau hari raya.</p>
                    </div>

                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
                      <div>
                        <label style={{ marginBottom: '4px' }}>Terapkan Holiday Effect</label>
                        <span className="help-text" style={{ marginTop: 0 }}>Gunakan data libur pada prediksi selanjutnya.</span>
                      </div>
                      <label className="switch" style={{ cursor: 'pointer' }}>
                        <div style={{ width: '48px', height: '24px', background: 'var(--color-success)', borderRadius: '100px', position: 'relative' }}>
                          <div style={{ width: '20px', height: '20px', background: 'white', borderRadius: '50%', position: 'absolute', right: '2px', top: '2px' }}></div>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="table-wrapper" style={{ marginTop: '24px' }}>
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>Waktu Eksekusi</th>
                        <th>Proses Pipeline</th>
                        <th>Baris Diproses</th>
                        <th>Durasi</th>
                        <th>Status Validasi</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>03 Jun 2026, 08:15</td>
                        <td>Transformasi ke Format Time-Series (Aggregasi Harian)</td>
                        <td>12,450 baris</td>
                        <td>1.2s</td>
                        <td><span className="badge badge-aman">Sukses</span></td>
                      </tr>
                      <tr>
                        <td>03 Jun 2026, 08:14</td>
                        <td>Imputasi Missing Values (Forward Fill)</td>
                        <td>15,800 baris</td>
                        <td>0.8s</td>
                        <td><span className="badge badge-aman">Sukses</span></td>
                      </tr>
                      <tr>
                        <td>03 Jun 2026, 08:14</td>
                        <td>Identifikasi & Penghapusan Duplikasi</td>
                        <td>15,887 baris</td>
                        <td>2.4s</td>
                        <td><span className="badge badge-aman">Sukses</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {activeTab === 'prediction' && (
              <section className="prediction-section fade-in">
                <div className="section-header">
                  <h2>Simulasi <span>Prediksi Baru</span></h2>
                </div>

                <div className="charts-section" style={{ gridTemplateColumns: '1fr 1.5fr' }}>
                  <div className="big-card settings-card" style={{ margin: 0 }}>
                    <div className="settings-intro">
                      <h3>Unggah Dataset</h3>
                      <p className="desc">Masukkan file data historis penjualan atau fitur pendukung lainnya (Format CSV/XLSX).</p>
                    </div>

                    <div className="file-upload-box">
                      <div className="upload-icon">📄</div>
                      <p>Drag & drop file dataset ke sini, atau <strong>Pilih File</strong></p>
                      <span className="help-text">Maksimal ukuran file: 50MB</span>
                    </div>

                    <div className="form-divider" style={{ margin: '24px 0' }}></div>

                    <form onSubmit={handleRunPrediction}>
                      <div className="form-group">
                        <label>Pilih Algoritma Estimasi</label>
                        <select className="form-control" defaultValue="prophet">
                          <option value="prophet">Facebook Prophet</option>
                          <option value="arima">ARIMA Model</option>
                          <option value="lstm">LSTM Neural Network</option>
                        </select>
                      </div>

                      <div className="form-group" style={{ marginTop: '16px' }}>
                        <label>Target Variabel (Y)</label>
                        <input type="text" className="form-control" placeholder="Contoh: total_sales, quantity_demanded" required />
                      </div>

                      <div className="form-group" style={{ marginTop: '16px' }}>
                        <label>Horizon Prediksi (Hari)</label>
                        <select className="form-control" defaultValue="30">
                          <option value="30">30 Hari Kedepan</option>
                          <option value="60">60 Hari Kedepan</option>
                          <option value="90">90 Hari Kedepan</option>
                        </select>
                      </div>

                      <button 
                        type="submit" 
                        className="btn-primary" 
                        style={{ width: '100%', marginTop: '24px' }}
                        disabled={isPredicting}
                      >
                        {isPredicting ? 'Menganalisis Data...' : 'Jalankan Model AI'}
                      </button>
                    </form>
                  </div>

                  <div className="big-card result-panel">
                    {isPredicting ? (
                      <div className="loading-result">
                        <div className="spinner"></div>
                        <p>Model sedang mengekstraksi Feature Importance dan memproses forecasting...</p>
                      </div>
                    ) : predictionResult ? (
                      <div className="result-content fade-in">
                        <div className="card-header" style={{ marginBottom: '24px' }}>
                          <h3>Hasil Proyeksi Estimasi</h3>
                          <span className="tag-small success-tag">Berhasil ({predictionResult.confidenceScore} Conf.)</span>
                        </div>
                        
                        <div className="canvas-container" style={{ height: '240px' }}>
                          <Line options={chartOptions} data={predictionResult} />
                        </div>

                        <div className="result-insight-box mt-4">
                          <p><strong>Insight Bisnis:</strong> {predictionResult.recommendedAction}</p>
                          <p className="help-text">Deteksi Anomali Potensial: {predictionResult.estimatedAnomalies} titik data.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="empty-state">
                        <div className="empty-icon">📊</div>
                        <p>Hasil prediksi akan muncul di sini setelah model selesai dijalankan.</p>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'settings' && (
              <section className="settings-section fade-in">
                <div className="section-header">
                  <h2>Konfigurasi <span>Prophet AI</span></h2>
                </div>
                
                <div className="big-card settings-card">
                  <div className="settings-intro">
                    <h3>Parameter Model Time Series</h3>
                    <p className="desc">Sesuaikan sensitivitas model AI terhadap perubahan tren data historis.</p>
                  </div>
                  
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Changepoint Prior Scale</label>
                      <input type="number" step="0.01" defaultValue="0.05" className="form-control" />
                      <span className="help-text">Menentukan fleksibilitas tren.</span>
                    </div>

                    <div className="form-group">
                      <label>Seasonality Prior Scale</label>
                      <input type="number" step="0.01" defaultValue="10.0" className="form-control" />
                    </div>

                    <div className="form-group">
                      <label>Seasonality Mode</label>
                      <select className="form-control" defaultValue="additive">
                        <option value="additive">Additive</option>
                        <option value="multiplicative">Multiplicative</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Periode Prediksi Global (Hari)</label>
                      <input type="number" defaultValue="7" className="form-control" />
                    </div>
                  </div>

                  <div className="form-divider"></div>

                  <div className="form-actions">
                    <button className="btn-secondary">Kembalikan ke Default</button>
                    <button className="btn-primary">Simpan & Retrain Model</button>
                  </div>
                </div>
              </section>
            )}

          </div>
        )}
      </div>
    </div>
  );
};

export default App;