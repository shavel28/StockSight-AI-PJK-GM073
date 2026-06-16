import React, { useState, useEffect } from 'react';

const Login = ({ setToken }) => {
  const [isLoginMode, setIsLoginMode] = useState(true); 
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState({ text: '', type: '' });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkExistingSession = async () => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        try {
          const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/auth/session', {
            headers: { 'Authorization': `Bearer ${savedToken}` }
          });
          
          if (response.ok) {
            setToken(savedToken);
          } else {
            localStorage.removeItem('token');
          }
        } catch (err) {
          console.error("Gagal mengecek sesi:", err);
        }
      }
    };
    
    checkExistingSession();
  }, [setToken]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      if (isLoginMode) {
        const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        
        const data = await response.json();

        if (response.ok) {
          localStorage.setItem('token', data.access_token);
          setToken(data.access_token); 
        } else {
          setMessage({ text: data.detail || 'Login gagal. Periksa email dan password.', type: 'error' });
        }
      } else {
        const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password }),
        });

        if (response.ok) {
          setMessage({ text: 'Pendaftaran berhasil! Silakan masuk dengan akun Anda.', type: 'success' });
          setIsLoginMode(true); 
          setPassword(''); 
        } else {
          const data = await response.json();
          setMessage({ text: data.detail || 'Gagal mendaftar. Email mungkin sudah digunakan.', type: 'error' });
        }
      }
    } catch (err) {
      setMessage({ text: 'Gagal terhubung ke server backend. Pastikan server menyala.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-wrapper" style={{ alignItems: 'center' }}>
      <div className="big-card settings-card" style={{ maxWidth: '400px', width: '100%', padding: '40px' }}>
        <div className="logo" style={{ justifyContent: 'center', marginBottom: '32px' }}>
          <img src="/logo.png" alt="Stocksight AI" className="logo-img" />
          <span style={{ fontSize: '1.5rem' }}>Stocksight AI</span>
        </div>
        
        <div className="settings-intro" style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h3>{isLoginMode ? 'Selamat Datang' : 'Buat Akun Baru'}</h3>
          <p className="desc">
            {isLoginMode ? 'Silakan masuk ke akun Anda' : 'Lengkapi data di bawah untuk mendaftar'}
          </p>
        </div>

        {message.text && (
          <div style={{ 
            backgroundColor: message.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', 
            color: message.type === 'error' ? 'var(--color-danger)' : 'var(--color-success)', 
            padding: '12px', borderRadius: '8px', marginBottom: '20px', fontSize: '0.9rem', textAlign: 'center' 
          }}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLoginMode && (
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label>Nama Lengkap</label>
              <input 
                type="text" 
                className="form-control" 
                placeholder="Nama Lengkap"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required={!isLoginMode} 
              />
            </div>
          )}

          <div className="form-group">
            <label>Email</label>
            <input 
              type="email" 
              className="form-control" 
              placeholder="nama@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
          </div>

          <div className="form-group" style={{ marginTop: '16px' }}>
            <label>Password</label>
            <input 
              type="password" 
              className="form-control" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>

          <button 
            type="submit" 
            className="btn-primary" 
            style={{ width: '100%', marginTop: '32px', marginBottom: '16px' }}
            disabled={isLoading}
          >
            {isLoading 
              ? 'Memproses...' 
              : (isLoginMode ? 'Masuk ke Dashboard' : 'Daftar Akun')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          {isLoginMode ? "Belum punya akun? " : "Sudah punya akun? "}
          <button 
            type="button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setMessage({ text: '', type: '' }); 
            }}
            style={{
              background: 'none', border: 'none', color: 'var(--primary)', 
              fontWeight: 'bold', cursor: 'pointer', padding: 0
            }}
          >
            {isLoginMode ? 'Daftar di sini' : 'Masuk di sini'}
          </button>
        </div>

      </div>
    </div>
  );
};

export default Login;