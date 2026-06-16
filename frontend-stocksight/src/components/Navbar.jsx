import React from 'react';

const Navbar = ({ activeTab, setActiveTab, setToken }) => {

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null); 
  };

  return (
    <header className="navbar">
      <div className="logo">
        <img src="/logo.png" alt="Stocksight AI" className="logo-img" />
        <span>Stocksight AI</span>
      </div>
      <nav className="nav-links">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Utama</button>
        <button className={activeTab === 'inventory' ? 'active' : ''} onClick={() => setActiveTab('inventory')}>Inventori</button>
        <button className={activeTab === 'data-prep' ? 'active' : ''} onClick={() => setActiveTab('data-prep')}>Data Pipeline</button>
        <button className={activeTab === 'prediction' ? 'active' : ''} onClick={() => setActiveTab('prediction')}>Prediksi Baru</button>
        <button className={activeTab === 'settings' ? 'active' : ''} onClick={() => setActiveTab('settings')}>Config AI</button>
      </nav>
      
      <div className="user-profile">
        <div className="avatar">PJK</div>
        <span className="user-name">PJK-GM073</span>
        <button 
          onClick={handleLogout} 
          style={{ background: 'none', border: '1px solid var(--color-danger)', color: 'var(--color-danger)', padding: '6px 12px', borderRadius: '100px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 'bold', marginLeft: '8px' }}
        >
          Keluar
        </button>
      </div>
    </header>
  );
};

export default Navbar;