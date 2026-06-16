import React, { useState, useEffect } from 'react';

const Inventory = ({ token }) => {
  const [inventoryList, setInventoryList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const handleAddStock = async (product) => {
    const newStock = prompt(`Masukkan jumlah stok fisik terbaru untuk kategori "${product.name}":`, product.currentStock);
    
    if (newStock !== null && !isNaN(newStock)) {
      try {
        const response = await fetch(`https://stocksightcapstone-production.up.railway.app/api/v1/products/${product.originalId}/stock`, {
          method: 'PATCH',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ current_stock: parseInt(newStock) })
        });

        if (response.ok) {
          fetchInventory(); 
        } else {
          alert("Gagal memperbarui stok di server.");
        }
      } catch (error) {
        alert("Error koneksi jaringan.");
      }
    }
  };

  const fetchInventory = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('https://stocksightcapstone-production.up.railway.app/api/v1/inventory/reorder', {
        headers: { 'Authorization': `Bearer ${token}` }
      }); 
      
      if (!response.ok) throw new Error('Gagal menarik data');
      const data = await response.json();
      
      const uniqueDataMap = new Map();
      data.forEach(item => {
        if (!uniqueDataMap.has(item.product_name)) {
            uniqueDataMap.set(item.product_name, item);
        }
      });

      const formattedData = Array.from(uniqueDataMap.values()).map(item => {
        let badgeStatus = 'Aman';
        if (item.current_stock <= item.safety_stock) badgeStatus = 'Kritis';
        else if (item.current_stock <= item.reorder_point) badgeStatus = 'Stok Rendah';

        return {
          originalId: item.product_id, 
          id: item.product_id.split('-')[0].toUpperCase(),
          name: item.product_name,
          currentStock: item.current_stock,
          reorderPoint: item.reorder_point || 0,
          safetyStock: item.safety_stock || 0,
          status: badgeStatus
        };
      });
      
      setInventoryList(formattedData); 
    } catch (error) {
      console.error("Error Fetching:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [token]);

  if (isLoading) return <div className="loader">Menyinkronkan data gudang...</div>;

  const itemsKritis = inventoryList.filter(i => i.status === 'Kritis');
  const itemsRendah = inventoryList.filter(i => i.status === 'Stok Rendah');

  return (
    <section className="table-section fade-in">
      {(itemsKritis.length > 0 || itemsRendah.length > 0) && (
        <div style={{ marginBottom: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {itemsKritis.length > 0 && (
            <div style={{ backgroundColor: '#FEF2F2', borderLeft: '6px solid var(--color-danger)', padding: '16px', borderRadius: '8px', color: '#991B1B' }}>
              <strong>🚨 STATUS KRITIS:</strong> Stok untuk <b>{itemsKritis.map(i => i.name).join(', ')}</b> sudah menyentuh batas Safety Stock! Segera lakukan pemesanan ulang (Restock).
            </div>
          )}
          {itemsRendah.length > 0 && (
            <div style={{ backgroundColor: '#FFFBEB', borderLeft: '6px solid var(--color-warning)', padding: '16px', borderRadius: '8px', color: '#92400E' }}>
              <strong>⚠️ PERHATIAN:</strong> Stok <b>{itemsRendah.map(i => i.name).join(', ')}</b> sudah di bawah titik Reorder Point (ROP). Siapkan pengadaan barang.
            </div>
          )}
        </div>
      )}

      <div className="section-header">
        <div>
          <h2>Manajemen <span>Inventaris</span></h2>
          <p className="desc" style={{marginBottom: 0, marginTop: '4px'}}>Pantau indikator ketersediaan stok fisik terhadap parameter batas aman pergudangan.</p>
        </div>
        <div className="header-actions-inline">
          <button className="btn-secondary" onClick={fetchInventory}>Refresh</button>
        </div>
      </div>

      <div className="charts-section" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '24px' }}>
        <div className="big-card" style={{ padding: '24px', backgroundColor: 'var(--bg-page)' }}>
          <h4 style={{ marginBottom: '8px', color: 'var(--primary)' }}>Tingkat Pemesanan Ulang (ROP)</h4>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Titik di mana sistem merekomendasikan pengadaan barang baru agar stok tetap tersedia selama masa pengiriman pesanan (Lead Time).
          </p>
          <code style={{ display: 'block', backgroundColor: 'var(--white)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
            ROP = (Average Daily Demand × Lead Time) + Safety Stock
          </code>
        </div>
        <div className="big-card" style={{ padding: '24px', backgroundColor: 'var(--bg-page)' }}>
          <h4 style={{ marginBottom: '8px', color: 'var(--accent-cyan)' }}>Stok Pengaman (Safety Stock)</h4>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Batas pertahanan terakhir pergudangan untuk mengantisipasi fluktuasi permintaan tak terduga (diukur dengan IQR & Standard Deviation).
          </p>
          <code style={{ display: 'block', backgroundColor: 'var(--white)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
            Safety Stock = Z × Standard Deviation Demand × √Lead Time
          </code>
        </div>
      </div>
      
      <div className="table-wrapper">
        <table className="modern-table">
          <thead>
            <tr>
              <th>ID Validasi</th><th>Kategori Produk</th><th>Stok Tersedia</th><th>Safety Stock</th><th>Batas Restock (ROP)</th><th>Kondisi</th><th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {inventoryList.length > 0 ? inventoryList.map((item, index) => (
              <tr key={index}>
                <td><span className="id-tag">{item.id}</span></td>
                <td><strong>{item.name}</strong></td>
                <td><strong style={{ fontSize: '1.1rem', color: item.status === 'Kritis' ? 'var(--color-danger)' : (item.status === 'Stok Rendah' ? 'var(--color-warning)' : 'inherit') }}>{item.currentStock}</strong></td>
                <td>{item.safetyStock}</td>
                <td>{item.reorderPoint}</td>
                <td>
                  <span className={`badge badge-${item.status.toLowerCase().replace(' ', '-')}`}>
                    {item.status}
                  </span>
                </td>
                <td>
                  <button 
                    className="btn-secondary" 
                    style={{ padding: '6px 14px', fontSize: '0.85rem' }}
                    onClick={() => handleAddStock(item)}
                  >
                    Ubah Stok
                  </button>
                </td>
              </tr>
            )) : (
              <tr><td colSpan="7" style={{textAlign: 'center', padding: '40px'}}>Data kosong. Harap sinkronisasi file CSV.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default Inventory;