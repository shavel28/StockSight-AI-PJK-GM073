import React, { useState, useEffect } from 'react';

const Settings = ({ token }) => {
  const defaultValues = {
    default_horizon: 30,
    forecast_scenario: 'expected',
    growth_factor: 0.0
  };
  const [config, setConfig] = useState(defaultValues);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/config', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
  
          setConfig({ ...defaultValues, ...data });
        }
      } catch (error) {
        console.error("Gagal menarik konfigurasi AI:", error);
      }
    };
    if (token) fetchConfig();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: name === 'forecast_scenario' ? value : Number(value)
    }));
  };

  const handleResetDefault = async () => {
    setConfig(defaultValues);
    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(defaultValues)
      });

      if (response.ok) {
        setMessage({ 
          text: 'Skenario bisnis berhasil dikembalikan ke mode Normal (Default)!', 
          type: 'success' 
        });
      } else {
        setMessage({ text: 'Gagal mereset skenario di server.', type: 'error' });
      }
    } catch (error) {
      setMessage({ text: 'Gagal terhubung ke server.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        window.dispatchEvent(
          new Event("configUpdated")
        );

        setMessage({
          text: 'Skenario Bisnis berhasil diterapkan! Silakan cek hasil baru di menu Prediksi.',
          type: 'success'
        });
      } else {
        setMessage({ text: 'Gagal menyimpan skenario.', type: 'error' });
      }
    } catch (error) {
      setMessage({ text: 'Gagal terhubung ke server.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="settings-section fade-in">
      <div className="section-header">
        <h2>Simulasi <span>Skenario Bisnis</span></h2>
      </div>
      
      <div className="big-card settings-card">
        <div className="settings-intro">
          <h3>Parameter Estimasi</h3>
          <p className="desc">Ubah asumsi pasar untuk melihat bagaimana pengaruhnya terhadap prediksi AI.</p>
        </div>

        {message.text && (
          <div style={{ 
            backgroundColor: message.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', 
            color: message.type === 'error' ? 'var(--color-danger)' : 'var(--color-success)', 
            padding: '12px', borderRadius: '8px', marginBottom: '24px', fontSize: '0.9rem', textAlign: 'center', fontWeight: 'bold' 
          }}>
            {message.text}
          </div>
        )}
        
        <div className="form-grid">
          
          <div className="form-group">
            <label>Skenario Kondisi Pasar (AI Bounds)</label>
            <select 
              className="form-control" 
              name="forecast_scenario"
              value={config.forecast_scenario}
              onChange={handleChange}
            >
              <option value="expected">Normal / Sesuai Tren (Expected)</option>
              <option value="optimistic">Skenario Optimis (Batas Atas AI)</option>
              <option value="pessimistic">Skenario Pesimis (Batas Bawah AI)</option>
            </select>
            <span className="help-text">Gunakan rentang kepercayaan batas atas/bawah dari model ML.</span>
          </div>

          <div className="form-group">
            <label>Asumsi Pertumbuhan Eksternal (%)</label>
            <input 
              type="number" step="1" min="-100" max="500"
              className="form-control" 
              name="growth_factor"
              value={config.growth_factor}
              onChange={handleChange}
            />
            <span className="help-text">Suntikkan persentase manual (Misal: ketik 10 untuk +10%).</span>
          </div>

          <div className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label>Periode Prediksi Global (Hari)</label>
            <input 
              type="number" min="1" max="365"
              className="form-control" 
              name="default_horizon"
              value={config.default_horizon}
              onChange={handleChange}
            />
            <span className="help-text">Berapa hari ke depan prediksi ingin dijalankan secara global.</span>
          </div>

        </div>

        <div className="form-divider"></div>

        <div className="form-actions">
          <button 
            type="button"
            className="btn-secondary" 
            onClick={handleResetDefault}
            disabled={isLoading}
          >
            {isLoading ? 'Mereset...' : 'Kembalikan ke Normal'}
          </button>
          
          <button 
            type="button"
            className="btn-primary" 
            onClick={handleSave} 
            disabled={isLoading}
          >
            {isLoading ? 'Menyimpan...' : 'Terapkan Skenario'}
          </button>
        </div>
      </div>
    </section>
  );
};

export default Settings;