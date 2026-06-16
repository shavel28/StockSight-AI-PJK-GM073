import React, { useState } from 'react';
import './App.css';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler } from 'chart.js';

import Navbar from './components/Navbar';
import Overview from './pages/Overview';
import Inventory from './pages/Inventory';
import DataPipeline from './pages/DataPipeline';
import Prediction from './pages/Prediction';     
import Settings from './pages/Settings';
import Login from './pages/Login'; 

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('overview');

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,

    interaction: {
      mode: 'index',
      intersect: false,
    },

    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          boxWidth: 8,
          font: { family: 'News Cycle' }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleFont: {
          size: 14,
          family: 'News Cycle'
        },
        bodyFont: {
          size: 13,
          family: 'News Cycle'
        },
        padding: 12,
        cornerRadius: 8,
      }
    },

    scales: {
      y: {
        grid: {
          borderDash: [4, 4],
          color: '#E2E8F0'
        },
        ticks: {
          font: { family: 'News Cycle' }
        }
      },
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: { family: 'News Cycle' },
          autoSkip: false,
          maxRotation: 45,
          minRotation: 45
        }
      }
    }
  };

  if (!token) {
    return <Login setToken={setToken} />;
  }

  return (
    <div className="page-wrapper">
      <div className="app-container">
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} setToken={setToken} />

        <div className="tab-content fade-in">
          {activeTab === 'overview' && <Overview chartOptions={chartOptions} token={token} setActiveTab={setActiveTab} />}
          {activeTab === 'inventory' && <Inventory token={token} />}
          {activeTab === 'data-prep' && <DataPipeline />}
          {activeTab === 'prediction' && <Prediction chartOptions={chartOptions} token={token} />}
          {activeTab === 'settings' && <Settings token={token} />}
        </div>
      </div>
    </div>
  );
};

export default App;