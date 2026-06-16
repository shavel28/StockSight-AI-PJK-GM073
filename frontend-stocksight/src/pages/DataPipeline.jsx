import React, { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';

const DataPipeline = () => {
  const [outliers, setOutliers] = useState([]);
  const [events, setEvents] = useState(null);
  const [monthly, setMonthly] = useState([]);
  const [features, setFeatures] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPipelineData = async () => {
      try {
        setIsLoading(true);
        const [outRes, evRes, monRes, featRes] = await Promise.all([
          fetch('https://stocksightcapstone-production.up.railway.app/api/v1/pipeline/outliers'),
          fetch('https://stocksightcapstone-production.up.railway.app/api/v1/pipeline/events'),
          fetch('https://stocksightcapstone-production.up.railway.app/api/v1/pipeline/monthly'),
          fetch('https://stocksightcapstone-production.up.railway.app/api/v1/pipeline/features')
        ]);

        if (outRes.ok) setOutliers(await outRes.json());
        if (evRes.ok) setEvents(await evRes.json());
        if (monRes.ok) setMonthly(await monRes.json());
        if (featRes.ok) setFeatures(await featRes.json());
      } catch (error) {
        console.error("Gagal menarik data visualisasi pipeline:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPipelineData();
  }, []);

 
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false, 
    },
    plugins: { 
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleFont: { size: 14, family: 'News Cycle' },
        bodyFont: { size: 14, family: 'News Cycle' },
        padding: 12,
        cornerRadius: 8,
        displayColors: false, 
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('id-ID', { maximumFractionDigits: 1 }).format(context.parsed.y);
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: { grid: { borderDash: [4, 4], color: '#E2E8F0' } },
      x: { grid: { display: false } }
    }
  };

  const outlierChart = {
    labels: outliers.map(o => o.Category),
    datasets: [{
      label: 'Jumlah Anomali',
      data: outliers.map(o => o['Outlier Count']),
      backgroundColor: '#EF4444',
      borderRadius: 6
    }]
  };

  const eventChart = {
    labels: ['Hari Biasa', 'Ada Promo', 'Hari Libur'],
    datasets: [{
      label: 'Rata-rata Penjualan',
      data: events ? [
        events.promo_impact?.normal || 0, 
        events.promo_impact?.promo || 0, 
        events.holiday_impact?.holiday || 0
      ] : [0,0,0],
      backgroundColor: ['#94A3B8', '#3B82F6', '#10B981'],
      borderRadius: 6
    }]
  };

  const monthlyChart = {
    labels: monthly.map(m => m.ds),
    datasets: [{
      label: 'Total Terjual',
      data: monthly.map(m => m.y),
      borderColor: '#7C3AED',
      backgroundColor: 'rgba(124, 58, 237, 0.1)',
      borderWidth: 3,
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#7C3AED',
      pointRadius: 4,       
      pointHoverRadius: 7, 
      pointBorderColor: '#FFFFFF',
      pointBorderWidth: 2
    }]
  };

  if (isLoading) return <div className="loader">Menyusun Dasbor Pipeline Data...</div>;

  return (
    <section className="prediction-section fade-in">
      <div className="section-header">
        <div>
          <h2>Panduan & Aturan <span>Data CSV</span></h2>
          <p className="desc" style={{marginBottom: 0, marginTop: '4px'}}>Ketentuan wajib dan wawasan mendalam dari data sebelum masuk ke mesin AI.</p>
        </div>
      </div>

      <div className="charts-section" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '24px' }}>
        <div className="big-card">
          <div className="card-header" style={{ marginBottom: '24px' }}>
            <h3>Format Kolom Mutlak (Wajib)</h3>
            <span className="tag-small success-tag">Wajib Ada</span>
          </div>
          <p className="desc">File Excel/CSV yang kamu unggah <b>harus secara persis</b> memiliki nama judul kolom berikut:</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '16px', background: 'var(--bg-page)', borderRadius: '12px', borderLeft: '5px solid var(--color-danger)' }}>
              <strong style={{ fontSize: '1.1rem' }}>Category</strong> 
              <p className="help-text" style={{marginTop:'6px', color:'var(--text-primary)'}}>Kategori produk (Contoh: Furniture, Office Supplies, Technology).</p>
            </div>
            <div style={{ padding: '16px', background: 'var(--bg-page)', borderRadius: '12px', borderLeft: '5px solid var(--primary)' }}>
              <strong style={{ fontSize: '1.1rem' }}>ds</strong> 
              <p className="help-text" style={{marginTop:'6px', color:'var(--text-primary)'}}>Tanggal penjualan, format: YYYY-MM-DD.</p>
            </div>
            <div style={{ padding: '16px', background: 'var(--bg-page)', borderRadius: '12px', borderLeft: '5px solid var(--color-success)' }}>
              <strong style={{ fontSize: '1.1rem' }}>y</strong> 
              <p className="help-text" style={{marginTop:'6px', color:'var(--text-primary)'}}>Jumlah barang yang terjual (angka bulat/desimal).</p>
            </div>
          </div>
        </div>

        <div className="big-card">
          <div className="card-header" style={{ marginBottom: '24px' }}>
            <h3>Tren Makro Penjualan Bulanan</h3>
            <span className="tag-small">12 Bulan Terakhir</span>
          </div>
          <p className="desc">Pola pertumbuhan bisnis agregat yang sudah difilter dari fluktuasi (noise) harian.</p>
          <div className="canvas-container">
            {monthly.length > 0 ? <Line data={monthlyChart} options={chartOptions} /> : <p className="help-text">Data bulanan tidak ditemukan.</p>}
          </div>
        </div>
      </div>

      <div className="charts-section" style={{ gridTemplateColumns: '1fr 1.5fr', marginBottom: '24px' }}>
        <div className="big-card">
          <div className="card-header" style={{ marginBottom: '24px' }}>
            <h3>Deteksi Anomali Volatilitas</h3>
            <span className="tag-small" style={{color: '#EF4444', borderColor: '#EF4444'}}>Outlier</span>
          </div>
          <p className="desc">Total hari di mana terjadi lonjakan tajam atau penurunan tidak wajar per kategori.</p>
          <div className="canvas-container" style={{ height: '240px' }}>
            {outliers.length > 0 ? <Bar data={outlierChart} options={chartOptions} /> : <p className="help-text">Data outlier tidak ditemukan.</p>}
          </div>
        </div>

        <div className="big-card">
          <div className="card-header" style={{ marginBottom: '24px' }}>
            <h3>Analisis Dampak Event (Regressors)</h3>
            <span className="tag-small" style={{color: '#3B82F6', borderColor: '#3B82F6'}}>Marketing Insight</span>
          </div>
          <p className="desc">Perbandingan efektivitas kampanye promosi dan hari libur terhadap rata-rata unit terjual harian.</p>
          <div className="canvas-container" style={{ height: '240px' }}>
            {events ? <Bar data={eventChart} options={chartOptions} /> : <p className="help-text">Data event tidak ditemukan.</p>}
          </div>
        </div>
      </div>


      <div className="table-wrapper" style={{ marginTop: '24px' }}>
        <div className="card-header" style={{ marginBottom: '16px' }}>
          <h3>Transparansi Data AI (Feature Engineering)</h3>
        </div>
        <p className="desc">Cuplikan bagaimana sistem merapikan data mentah sebelum diproses AI (Pembersihan Outlier & Pembuatan Lag).</p>
        <table className="modern-table" style={{ marginBottom: '40px' }}>
          <thead>
            <tr>
              <th>Tanggal</th><th>Kategori</th><th>Y Original</th><th>Y Capped (Dibersihkan)</th><th>Rolling Mean (7D)</th><th>Lag 1 (Kemarin)</th>
            </tr>
          </thead>
          <tbody>
            {features.length > 0 ? features.map((item, index) => (
              <tr key={index}>
                <td><span className="id-tag">{item.ds}</span></td>
                <td><strong>{item.Category}</strong></td>
                <td>{item.y_original?.toFixed(2)}</td>
                <td><span style={{color: 'var(--color-success)', fontWeight: 'bold'}}>{item.y_capped?.toFixed(2)}</span></td>
                <td>{item.rolling_mean_7?.toFixed(2)}</td>
                <td>{item.lag_1?.toFixed(2)}</td>
              </tr>
            )) : (
              <tr><td colSpan="6" style={{textAlign: 'center', padding: '20px'}}>Data Feature Engineering belum tersedia.</td></tr>
            )}
          </tbody>
        </table>

        <div className="card-header" style={{ marginBottom: '16px' }}>
          <h3>Status Layanan Pipeline Backend</h3>
        </div>
        <table className="modern-table">
          <thead>
            <tr>
              <th>Tahapan Data Pipeline (Backend)</th>
              <th>Status Layanan</th>
              <th>Fungsi Pustaka</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Validasi Skema (ds, y, Category) & Tipe Data</td>
              <td><span className="badge badge-aman">Active</span></td>
              <td><code>pandas.to_datetime()</code></td>
            </tr>
            <tr>
              <td>Deduplikasi Master Kategori Produk</td>
              <td><span className="badge badge-aman">Active</span></td>
              <td><code>drop_duplicates(subset=["Category"])</code></td>
            </tr>
            <tr>
              <td>Injeksi Data Historis ke Model Mesin AI</td>
              <td><span className="badge badge-aman">Active</span></td>
              <td><code>Prophet.fit()</code></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default DataPipeline;