import React, { useState } from 'react';
import { AlertCircle, Clock, TrendingDown, BarChart3, ArrowRight } from 'lucide-react';

/**
 * StupidStuffTracker Component
 * Highlights redundant or wasteful EHR actions across the department
 * 
 * Shows:
 * - Unnecessary clicks/alerts per shift
 * - Estimated time wasted per week
 * - Ranked "De-implementation List"
 */

const StupidStuffTracker = ({ wasteData = [], onDrillDown }) => {
  const [expandedItem, setExpandedItem] = useState(null);

  // Mock data if none provided
  const defaultWasteData = [
    {
      id: 1,
      unit_id: 'ICU',
      issue: 'Duplicate vital sign entry flowsheets',
      description: 'Nurses entering vitals in both Epic and standalone monitor system',
      clicks_per_shift: 45,
      time_wasted_minutes: 18,
      affected_staff: 24,
      priority: 'high',
      recommendation: 'Enable auto-sync between monitor and EHR'
    },
    {
      id: 2,
      unit_id: 'ED',
      issue: 'Excessive medication alert overrides',
      description: '6 unnecessary alert screens per medication administration',
      clicks_per_shift: 38,
      time_wasted_minutes: 15,
      affected_staff: 32,
      priority: 'high',
      recommendation: 'Review alert fatigue settings with pharmacy'
    },
    {
      id: 3,
      unit_id: '4B',
      issue: 'Redundant patient status documentation',
      description: 'Same data entered in nursing notes AND flowsheet fields',
      clicks_per_shift: 28,
      time_wasted_minutes: 11,
      affected_staff: 18,
      priority: 'medium',
      recommendation: 'Consolidate documentation templates'
    },
    {
      id: 4,
      unit_id: 'ONC',
      issue: 'Manual chemotherapy calculation verification',
      description: 'Double-entry of weight-based dosing calculations',
      clicks_per_shift: 22,
      time_wasted_minutes: 9,
      affected_staff: 16,
      priority: 'medium',
      recommendation: 'Implement automated dose calculator'
    },
    {
      id: 5,
      unit_id: 'NICU',
      issue: 'Paper-to-digital transcription for I&O',
      description: 'Tracking intake/output on paper then entering into EHR',
      clicks_per_shift: 35,
      time_wasted_minutes: 14,
      affected_staff: 22,
      priority: 'high',
      recommendation: 'Deploy bedside mobile documentation'
    },
    {
      id: 6,
      unit_id: 'OR',
      issue: 'Multiple login sessions per procedure',
      description: 'Re-authentication required between OR systems',
      clicks_per_shift: 12,
      time_wasted_minutes: 8,
      affected_staff: 28,
      priority: 'low',
      recommendation: 'Implement SSO across perioperative systems'
    }
  ];

  const wasteList = wasteData.length > 0 ? wasteData : defaultWasteData;

  // Sort by time wasted (highest first)
  const sortedWaste = [...wasteList].sort((a, b) => b.time_wasted_minutes - a.time_wasted_minutes);

  // Calculate totals
  const totalWeeklyWaste = sortedWaste.reduce((sum, item) => sum + item.time_wasted_minutes * 5, 0); // 5 day work week
  const totalClicks = sortedWaste.reduce((sum, item) => sum + item.clicks_per_shift, 0);

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'medium':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'low':
        return 'bg-slate-50 text-slate-700 border-slate-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const handleExpand = (item) => {
    setExpandedItem(expandedItem?.id === item.id ? null : item);
    if (onDrillDown && expandedItem?.id !== item.id) {
      onDrillDown(item);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-sky-500" />
            Workflow Waste Tracker
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Redundant EHR actions costing staff time
          </p>
        </div>
        <BarChart3 className="w-6 h-6 text-slate-400" />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-red-50 rounded-lg border border-red-100">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-red-500" />
            <span className="text-xs font-medium text-red-700">Weekly Time Wasted</span>
          </div>
          <div className="text-2xl font-bold text-red-800">
            {Math.round(totalWeeklyWaste / 60)}h {totalWeeklyWaste % 60}m
          </div>
          <div className="text-xs text-red-600 mt-1">
            Across all tracked units
          </div>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="w-4 h-4 text-orange-500" />
            <span className="text-xs font-medium text-orange-700">Unnecessary Clicks</span>
          </div>
          <div className="text-2xl font-bold text-orange-800">
            {totalClicks}
          </div>
          <div className="text-xs text-orange-600 mt-1">
            Per shift average
          </div>
        </div>
      </div>

      {/* De-implementation List */}
      <div className="space-y-3">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <ArrowRight className="w-4 h-4" />
          De-implementation Priority List
        </h3>

        {sortedWaste.map((item, index) => (
          <div key={item.id}>
            <button
              onClick={() => handleExpand(item)}
              className={`w-full p-4 rounded-lg border text-left transition-all ${
                expandedItem?.id === item.id
                  ? 'bg-sky-50 border-sky-300 shadow-md'
                  : 'bg-white border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 text-slate-600 text-sm font-bold flex items-center justify-center">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-slate-800">{item.issue}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getPriorityStyles(item.priority)}`}>
                        {item.priority.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600">{item.unit_id} • {item.description}</div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-4">
                  <div className="text-lg font-bold text-red-600">{item.time_wasted_minutes}m</div>
                  <div className="text-xs text-slate-500">per shift</div>
                </div>
              </div>
            </button>

            {expandedItem?.id === item.id && (
              <div className="mt-2 ml-8 p-4 bg-white rounded-lg border border-slate-200 animate-in fade-in slide-in-from-top-2">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <span className="text-xs text-slate-500">Clicks/Shift</span>
                    <div className="font-semibold text-slate-800">{item.clicks_per_shift}</div>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">Staff Affected</span>
                    <div className="font-semibold text-slate-800">{item.affected_staff}</div>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">Weekly Impact</span>
                    <div className="font-semibold text-red-600">{item.time_wasted_minutes * 5} min</div>
                  </div>
                </div>
                <div className="p-3 bg-sky-50 rounded-lg border border-sky-100">
                  <span className="text-xs font-medium text-sky-700">RECOMMENDATION:</span>
                  <p className="text-sm text-sky-800 mt-1">{item.recommendation}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Potential Savings Callout */}
      <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
        <div className="flex items-start gap-3">
          <TrendingDown className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-green-800">Potential Time Recovery</h4>
            <p className="text-sm text-green-700 mt-1">
              Addressing top 3 issues could recover <strong>{Math.round(sortedWaste.slice(0, 3).reduce((s, i) => s + i.time_wasted_minutes, 0) * 5 / 60)} hours per week</strong> — equivalent to {Math.round(sortedWaste.slice(0, 3).reduce((s, i) => s + i.time_wasted_minutes, 0) * 5 / 480)} FTE.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StupidStuffTracker;
