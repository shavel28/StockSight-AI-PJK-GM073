import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

const Prediction = ({ chartOptions, token }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatusMsg, setUploadStatusMsg] = useState('');
  
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');

  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [insight, setInsight] = useState({});
  const [defaultHorizon, setDefaultHorizon] = useState(30);
  
  const delay = (ms) => new Promise(res => setTimeout(res, ms));

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/config', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setDefaultHorizon(data.default_horizon || 30);
        }
      } catch (err) {
        console.error("Gagal mengambil konfigurasi:", err);
      }
    };

    const fetchInitialProducts = async () => {
      try {
        const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/products', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          const uniqueProducts = [];
          const seenNames = new Set();
          for (const item of data) {
            if (!seenNames.has(item.product_name)) {
              seenNames.add(item.product_name);
              uniqueProducts.push(item);
            }
          }
          setProducts(uniqueProducts); 
          if (uniqueProducts.length > 0) setSelectedProductId(uniqueProducts[0].id);
        }
      } catch (error) {
        console.error("Gagal mengambil daftar produk:", error);
      }
    };

    if (token) {
      fetchConfig();
      fetchInitialProducts();
    }

    window.addEventListener("configUpdated", fetchConfig);
    return () => window.removeEventListener("configUpdated", fetchConfig);
  }, [token]);

  const handleUploadCSV = async (e) => {
    e.preventDefault();
    if (!selectedFile) { alert("Pilih file CSV terlebih dahulu!"); return; }

    setIsUploading(true);
    setUploadStatusMsg('Mengirim CSV ke server...');
    const formData = new FormData();
    formData.append('file', selectedFile); 

    try {
      const uploadRes = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/uploads', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      if (!uploadRes.ok) throw new Error("Gagal mengunggah file.");
      
      const uploadData = await uploadRes.json();
      setUploadStatusMsg('Menganalisis skema data CSV...');
      
      let isDone = false;
      for (let i = 0; i < 15; i++) { 
        const statusRes = await fetch(`https://stocksightcapstone-production.up.railway.app/api/v1/uploads/${uploadData.id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        const statusData = await statusRes.json();
        if (statusData.status === 'done') { isDone = true; break; } 
        else if (statusData.status === 'error') throw new Error("Format CSV tidak sesuai aturan data.");
        await delay(1500); 
      }

      if (!isDone) throw new Error("Waktu tunggu habis. File terlalu besar.");

      const prodRes = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/products', { headers: { 'Authorization': `Bearer ${token}` } });
      const prodData = await prodRes.json();
      
      const uniqueProducts = [];
      const seenNames = new Set();
      for (const item of prodData) {
        if (!seenNames.has(item.product_name)) {
          seenNames.add(item.product_name);
          uniqueProducts.push(item);
        }
      }

      setProducts(uniqueProducts); 
      if (uniqueProducts.length > 0) setSelectedProductId(uniqueProducts[0].id);
      setUploadStatusMsg('CSV sukses divalidasi! Sistem AI siap digunakan.');
    } catch (error) {
      alert(error.message);
      setUploadStatusMsg('');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunPrediction = async (e) => {
    e.preventDefault();

    if (!selectedProductId) return alert("Pilih produk terlebih dahulu!");

    setIsPredicting(true);
    setPredictionResult(null);

    try {
      const configRes = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/config', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      let horizon = defaultHorizon;
      if (configRes.ok) {
        const configData = await configRes.json();
        horizon = configData.default_horizon || defaultHorizon;
        setDefaultHorizon(horizon);
      }

      const forecastRes = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/forecasts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: selectedProductId,
          model: "prophet",
          horizon_days: horizon,
          include_holidays: true
        })
      });

      if (!forecastRes.ok) throw new Error("Gagal memanggil layanan AI.");

      const forecastData = await forecastRes.json();

      let isDone = false;
      for (let i = 0; i < 20; i++) {
        const statusRes = await fetch(`https://stocksightcapstone-production.up.railway.app/api/v1/forecasts/${forecastData.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const statusData = await statusRes.json();

        if (statusData.status === 'done') { isDone = true; break; }
        if (statusData.status === 'error') throw new Error("Gagal memproses grafik prediksi.");
        await delay(2000);
      }

      if (!isDone) throw new Error("Waktu komputasi AI habis.");

      const detailRes = await fetch(`https://stocksightcapstone-production.up.railway.app/api/v1/forecasts/${forecastData.id}/details`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const detailData = await detailRes.json();
      
      const hist = detailData.history || [];
      const fore = detailData.forecast || [];
      
      const allDates = [
        ...hist.map(d => d.date),
        ...fore.map(d => d.date).filter(date => !hist.some(h => h.date === date))
      ];
      
      const histMap = {};
      hist.forEach(d => { histMap[d.date] = d.qty; });

      const foreMap = {};
      fore.forEach(d => { foreMap[d.date] = d.qty; });

      const histValues = allDates.map(date => histMap[date] ?? null);
      const foreValues = allDates.map(date => foreMap[date] ?? null);

      if (hist.length > 0 && fore.length > 0) {
        foreValues[hist.length - 1] = histValues[hist.length - 1];
      }

      setPredictionResult({
        labels: allDates,
        datasets: [
          {
            label: 'Penjualan Historis',
            data: histValues,
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.05)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 6
          },
          {
            label: 'Prediksi AI',
            data: foreValues,
            borderColor: '#7C3AED',
            borderDash: [5, 5],
            backgroundColor: 'rgba(124, 58, 237, 0.15)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#7C3AED',
            pointRadius: 3,
            pointHoverRadius: 6
          }
        ]
      });

      const totalForecast = fore.reduce((sum, item) => sum + item.qty, 0);
      const avgForecast = fore.length > 0 ? (totalForecast / fore.length) : 0;
      const peakDay = fore.length > 0 ? fore.reduce((prev, current) => (prev.qty > current.qty) ? prev : current) : {qty: 0, date: '-'};

      setInsight({
        mape: detailData.mape,
        rmse: detailData.rmse,
        horizon: horizon,
        totalSales: totalForecast,
        avgSales: avgForecast,
        peakSales: peakDay.qty,
        peakDate: peakDay.date
      });

    } catch (error) {
      alert(error.message);
    } finally {
      setIsPredicting(false);
    }
  };

  const labelCount = predictionResult?.labels?.length || 0;
  const chartWidth = labelCount > 20 ? `${labelCount * 45}px` : "100%";

  return (
    <section className="prediction-section fade-in">
      <div className="section-header"><h2>Simulasi <span>Prediksi Baru</span></h2></div>

      <div className="charts-section" style={{ gridTemplateColumns: '1fr 2fr' }}>
        <div className="big-card settings-card" style={{ margin: 0 }}>
          
          <form onSubmit={handleUploadCSV}>
            <div className="settings-intro">
              <h3>1. Tambah Data Eksternal</h3>
              <p className="desc" style={{marginBottom: '16px'}}>Opsional: Unggah CSV jika ingin menguji dataset baru.</p>
            </div>
            
            <label className="file-upload-box" style={{display: 'block'}}>
              <input type="file" accept=".csv" onChange={(e) => setSelectedFile(e.target.files[0])} style={{display: 'none'}} />
              <div className="upload-icon">📄</div>
              <p>{selectedFile ? selectedFile.name : "Klik untuk Pilih File CSV"}</p>
            </label>

            <button type="submit" className="btn-secondary" style={{ width: '100%', marginTop: '16px' }} disabled={isUploading}>
              {isUploading ? uploadStatusMsg : 'Unggah & Proses Data CSV Baru'}
            </button>
            {uploadStatusMsg && !isUploading && <span className="help-text" style={{color: 'var(--color-success)', marginTop: '8px', display: 'block', textAlign: 'center'}}>{uploadStatusMsg}</span>}
          </form>

          <div className="form-divider" style={{ margin: '32px 0' }}></div>

          <form onSubmit={handleRunPrediction} style={{ opacity: products.length > 0 ? 1 : 0.4, pointerEvents: products.length > 0 ? 'auto' : 'none' }}>
            <div className="settings-intro">
              <h3>2. Model Forecasting (AI)</h3>
              <p className="desc" style={{marginBottom: '16px'}}>Menggunakan Pre-Trained Model dari Data Engineer.</p>
            </div>

            <div className="form-group">
              <label>Pilih Kategori untuk Diramal</label>
              <select className="form-control" value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.product_name}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginTop: '16px' }}>
              <label>Horizon Prediksi</label>
              <input type="text" className="form-control" value={`${defaultHorizon} Hari Ke Depan`} readOnly />
              <span className="help-text">Menggunakan durasi global dari menu Settings.</span>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '24px' }} disabled={isPredicting}>
              {isPredicting ? 'AI Sedang Menghitung...' : 'Jalankan Analisis AI'}
            </button>
          </form>
        </div>

        <div className="big-card result-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          {isPredicting ? (
            <div className="loading-result">
              <div className="spinner"></div>
              <p>Memuat model JSON dan menghitung probabilitas masa depan...</p>
            </div>
          ) : predictionResult ? (
            <div className="result-content fade-in" style={{ flex: 1 }}>
              <div className="card-header" style={{ marginBottom: '24px' }}>
                <h3>Hasil Analisis Tren & Prediksi</h3>
                <span className="tag-small success-tag">Selesai Dihitung</span>
              </div>
              
              <div style={{ width: "100%", overflowX: "auto", overflowY: "hidden", border: "1px solid #E2E8F0", borderRadius: "12px", marginBottom: '24px' }}>
                <div style={{ width: chartWidth, minWidth: "100%", height: "350px", position: "relative" }}>
                  <Line data={predictionResult} options={{ ...chartOptions, responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

                <div style={{ padding: '20px', background: 'var(--bg-page)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '12px', fontSize: '1.1rem' }}>Estimasi Permintaan ({insight.horizon} Hari)</h4>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: '2' }}>
                    <li>Total Proyeksi: <strong style={{fontSize: '1.1rem'}}>{new Intl.NumberFormat('id-ID').format(Math.round(insight.totalSales))} unit</strong></li>
                    <li>Rata-rata Harian: <strong>{new Intl.NumberFormat('id-ID').format(Math.round(insight.avgSales))} unit / hari</strong></li>
                    <li>Puncak Tertinggi: <strong>{new Intl.NumberFormat('id-ID').format(Math.round(insight.peakSales))} unit</strong> <br/><span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>Terjadi pada: {insight.peakDate}</span></li>
                  </ul>
                </div>

                <div style={{ padding: '20px', background: 'var(--bg-page)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ color: 'var(--accent-purple)', marginBottom: '12px', fontSize: '1.1rem' }}>Kualitas & Evaluasi AI</h4>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: '2' }}>

                    <li>MAPE Bulanan: <strong style={{ color: insight.mape < 25 ? 'var(--color-success)' : 'var(--color-warning)', fontSize: '1.1rem' }}>{insight.mape}%</strong></li>
                    <li>RMSE Bulanan: <strong>{new Intl.NumberFormat('id-ID').format(insight.rmse)}</strong></li>
                  </ul>
                  <p className="help-text" style={{ marginTop: '12px', fontSize: '0.8rem', lineHeight: '1.4' }}>
                    * <b>MAPE Bulanan</b> menunjukkan persentase deviasi model setelah menstabilkan fluktuasi (noise) harian. Digunakan untuk evaluasi pemesanan jangka panjang.
                  </p>
                </div>

              </div>

            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📈</div>
              <p>Pilih kategori produk di panel kiri dan jalankan AI untuk melihat grafik masa depan.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default Prediction;