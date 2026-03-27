import React, { useState } from 'react';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * RiskHeatmap Component
 * Grid view of all hospital units, color-coded by risk level
 * 
 * Color coding:
 * - Green = Low (0-39)
 * - Yellow = Medium (40-64)
 * - Orange = High (65-84)
 * - Red = Critical (85-100)
 */

const RiskHeatmap = ({ units = [], onUnitClick }) => {
  const [selectedUnit, setSelectedUnit] = useState(null);

  // Mock data if none provided
  const unitData = units.length > 0 ? units : [
    { unit_id: 'ICU', avg_score: 72, worker_count: 24, trend: 'worsening' },
    { unit_id: 'ED', avg_score: 58, worker_count: 32, trend: 'stable' },
    { unit_id: '4B', avg_score: 45, worker_count: 18, trend: 'improving' },
    { unit_id: 'PEDS', avg_score: 38, worker_count: 20, trend: 'improving' },
    { unit_id: 'ONC', avg_score: 67, worker_count: 16, trend: 'worsening' },
    { unit_id: 'NICU', avg_score: 52, worker_count: 22, trend: 'stable' },
    { unit_id: 'OR', avg_score: 81, worker_count: 28, trend: 'worsening' },
    { unit_id: 'PACU', avg_score: 43, worker_count: 14, trend: 'stable' },
  ];

  const getRiskLevel = (score) => {
    if (score >= 85) return { level: 'Critical', class: 'risk-critical' };
    if (score >= 65) return { level: 'High', class: 'risk-high' };
    if (score >= 40) return { level: 'Medium', class: 'risk-medium' };
    return { level: 'Low', class: 'risk-low' };
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'worsening':
        return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'improving':
        return <TrendingDown className="w-4 h-4 text-green-500" />;
      default:
        return <Minus className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleUnitClick = (unit) => {
    setSelectedUnit(unit);
    if (onUnitClick) onUnitClick(unit);
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-500" />
            Unit Risk Heatmap
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Real-time burnout risk across all units
          </p>
        </div>
        <div className="flex gap-2">
          <span className="badge risk-low">Low</span>
          <span className="badge risk-medium">Medium</span>
          <span className="badge risk-high">High</span>
          <span className="badge risk-critical">Critical</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {unitData.map((unit) => {
          const { level, class: riskClass } = getRiskLevel(unit.avg_score);
          
          return (
            <button
              key={unit.unit_id}
              onClick={() => handleUnitClick(unit)}
              className={`p-4 rounded-lg border-2 transition-all hover:scale-105 ${riskClass} ${
                selectedUnit?.unit_id === unit.unit_id ? 'ring-2 ring-sky-500 ring-offset-2' : ''
              }`}
            >
              <div className="text-left">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-lg">{unit.unit_id}</span>
                  {getTrendIcon(unit.trend)}
                </div>
                <div className="text-3xl font-bold mb-1">{unit.avg_score}</div>
                <div className="text-xs opacity-75">{level} Risk</div>
                <div className="text-xs mt-2 opacity-60">
                  {unit.worker_count} staff
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {selectedUnit && (
        <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <h3 className="font-semibold text-slate-700 mb-2">
            {selectedUnit.unit_id} Details
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-slate-500">Average Score:</span>
              <span className="ml-2 font-medium">{selectedUnit.avg_score}/100</span>
            </div>
            <div>
              <span className="text-slate-500">Staff Count:</span>
              <span className="ml-2 font-medium">{selectedUnit.worker_count}</span>
            </div>
            <div>
              <span className="text-slate-500">Trend:</span>
              <span className={`ml-2 font-medium capitalize ${
                selectedUnit.trend === 'worsening' ? 'text-red-600' :
                selectedUnit.trend === 'improving' ? 'text-green-600' :
                'text-slate-600'
              }`}>
                {selectedUnit.trend}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskHeatmap;
