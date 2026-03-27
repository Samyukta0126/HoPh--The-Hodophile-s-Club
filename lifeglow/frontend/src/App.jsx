import React, { useState, useEffect } from 'react';
import { Shield, Heart, Activity, Menu, X } from 'lucide-react';
import RiskHeatmap from './components/RiskHeatmap';
import PredictiveNudge from './components/PredictiveNudge';
import StupidStuffTracker from './components/StupidStuffTracker';

/**
 * LifeGLOW Dashboard - Unit Health Command Center
 * 
 * Main application component integrating all three dashboard views:
 * 1. RiskHeatmap - Unit-level burnout risk visualization
 * 2. PredictiveNudge - AI-generated manager recommendations
 * 3. StupidStuffTracker - Workflow waste identification
 */

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeView, setActiveView] = useState('dashboard');
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Mock system stats
  const [stats] = useState({
    totalUnits: 8,
    totalStaff: 174,
    criticalAlerts: 2,
    highRiskUnits: 2,
    avgBurnoutScore: 56.3,
    lastIngestion: new Date(Date.now() - 15 * 60 * 1000) // 15 min ago
  });

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleUnitClick = (unit) => {
    console.log('Unit selected:', unit);
    // In production: navigate to unit detail view or open modal
  };

  const handleActionTaken = (action) => {
    console.log('Action taken:', action);
    // In production: POST to /api/v1/interventions
  };

  const handleDrillDown = (item) => {
    console.log('Drilling down into:', item);
    // In production: open detailed analysis view
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md hover:bg-slate-100"
              >
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              
              <div className="flex items-center gap-2">
                <Heart className="w-8 h-8 text-sky-500 fill-sky-500" />
                <div>
                  <h1 className="text-xl font-bold text-slate-800">LifeGLOW</h1>
                  <p className="text-xs text-slate-500 hidden sm:block">
                    Predictive Burnout Monitoring System
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 text-sm text-slate-500">
                <Shield className="w-4 h-4" />
                <span>HIPAA Compliant</span>
              </div>
              <div className="hidden md:block text-right">
                <div className="text-sm font-medium text-slate-700">
                  Unit Health Command Center
                </div>
                <div className="text-xs text-slate-400">
                  Updated: {lastUpdated.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black/50" onClick={() => setSidebarOpen(false)}>
          <div className="fixed left-0 top-0 bottom-0 w-64 bg-white shadow-lg" onClick={e => e.stopPropagation()}>
            <nav className="p-4 space-y-2">
              <button
                onClick={() => { setActiveView('dashboard'); setSidebarOpen(false); }}
                className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 ${
                  activeView === 'dashboard' ? 'bg-sky-50 text-sky-700' : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Activity className="w-5 h-5" />
                Dashboard
              </button>
              <button
                onClick={() => { setActiveView('reports'); setSidebarOpen(false); }}
                className="w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-slate-600 hover:bg-slate-50"
              >
                <Shield className="w-5 h-5" />
                Compliance Reports
              </button>
            </nav>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <div className="text-sm text-slate-500 mb-1">Units Monitored</div>
            <div className="text-2xl font-bold text-slate-800">{stats.totalUnits}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <div className="text-sm text-slate-500 mb-1">Staff Protected</div>
            <div className="text-2xl font-bold text-slate-800">{stats.totalStaff}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-red-50 border p-4">
            <div className="text-sm text-red-600 mb-1">Critical Alerts</div>
            <div className="text-2xl font-bold text-red-700">{stats.criticalAlerts}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <div className="text-sm text-slate-500 mb-1">Avg Burnout Score</div>
            <div className="text-2xl font-bold text-slate-800">{stats.avgBurnoutScore}</div>
          </div>
        </div>

        {/* Privacy Notice */}
        <div className="mb-6 p-4 bg-sky-50 rounded-lg border border-sky-200">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sky-800">Privacy Protection Active</h3>
              <p className="text-sm text-sky-700 mt-1">
                Individual staff data is aggregated and anonymized. Personal information is only visible when 
                Critical threshold (>85) is exceeded, in compliance with HIPAA Safe Mode protocols.
              </p>
            </div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          <RiskHeatmap onUnitClick={handleUnitClick} />
          <PredictiveNudge onActionTaken={handleActionTaken} />
          <StupidStuffTracker onDrillDown={handleDrillDown} />
        </div>

        {/* Full-width section for larger screens */}
        <div className="mt-8 hidden lg:block">
          <div className="card">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">System Status</h3>
            <div className="grid grid-cols-4 gap-6 text-sm">
              <div>
                <span className="text-slate-500">Last Data Ingestion:</span>
                <div className="font-medium text-slate-700 mt-1">
                  {stats.lastIngestion.toLocaleString()}
                </div>
              </div>
              <div>
                <span className="text-slate-500">High-Risk Units:</span>
                <div className="font-medium text-orange-600 mt-1">{stats.highRiskUnits}</div>
              </div>
              <div>
                <span className="text-slate-500">Data Retention:</span>
                <div className="font-medium text-slate-700 mt-1">90 days (rolling)</div>
              </div>
              <div>
                <span className="text-slate-500">Compliance Mode:</span>
                <div className="font-medium text-green-600 mt-1">HIPAA + GDPR</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-slate-500">
              © 2025 LifeGLOW Health Systems. All rights reserved.
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-500">
              <span className="flex items-center gap-2">
                <Shield className="w-4 h-4" />
                HIPAA Compliant
              </span>
              <span className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                FHIR R4 Compatible
              </span>
              <span>v1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
