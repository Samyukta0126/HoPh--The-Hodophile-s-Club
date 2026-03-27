import React from 'react';
import { AlertTriangle, Clock, Users, CheckCircle } from 'lucide-react';

/**
 * PredictiveNudge Component
 * Displays auto-generated, actionable recommendations for managers
 * 
 * Shows:
 * - Unit name and risk score
 * - Recommended action
 * - Urgency badge
 */

const PredictiveNudge = ({ alerts = [], onActionTaken }) => {
  // Mock data if none provided
  const alertData = alerts.length > 0 ? alerts : [
    {
      unit_id: 'OR',
      avg_score: 85,
      risk_level: 'Critical',
      recommendation: 'Unit OR is at 85% risk — recommend 1 float nurse for Thursday shift. Current staff showing severe recovery debt.',
      urgency: 'critical',
      generated_at: new Date().toISOString()
    },
    {
      unit_id: 'ICU',
      avg_score: 72,
      risk_level: 'High',
      recommendation: 'Unit ICU showing consistent shift overruns (avg 52 min). Review staffing levels and assess patient acuity mix.',
      urgency: 'high',
      generated_at: new Date().toISOString()
    },
    {
      unit_id: 'ONC',
      avg_score: 67,
      risk_level: 'High',
      recommendation: 'Multiple staff filing notes 3+ hours post-shift. Consider documentation workflow optimization or EHR training.',
      urgency: 'high',
      generated_at: new Date().toISOString()
    },
    {
      unit_id: 'NICU',
      avg_score: 52,
      risk_level: 'Medium',
      recommendation: 'PTO utilization below department average. Proactively schedule time-off for staff with 60+ days without break.',
      urgency: 'medium',
      generated_at: new Date().toISOString()
    },
    {
      unit_id: 'ED',
      avg_score: 58,
      risk_level: 'Medium',
      recommendation: 'Break compliance at 75%. Implement protected break scheduling to improve recovery during shifts.',
      urgency: 'medium',
      generated_at: new Date().toISOString()
    }
  ];

  // Sort by risk score descending (most urgent first)
  const sortedAlerts = [...alertData].sort((a, b) => b.avg_score - a.avg_score);

  const getUrgencyStyles = (urgency) => {
    switch (urgency) {
      case 'critical':
        return {
          badge: 'bg-red-100 text-red-800 border-red-200',
          icon: 'text-red-500',
          border: 'border-l-4 border-red-500'
        };
      case 'high':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          icon: 'text-orange-500',
          border: 'border-l-4 border-orange-500'
        };
      case 'medium':
        return {
          badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          icon: 'text-yellow-500',
          border: 'border-l-4 border-yellow-500'
        };
      default:
        return {
          badge: 'bg-slate-100 text-slate-800 border-slate-200',
          icon: 'text-slate-500',
          border: 'border-l-4 border-slate-500'
        };
    }
  };

  const getRiskColor = (score) => {
    if (score >= 85) return 'text-red-600';
    if (score >= 65) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  const handleAccept = (alert) => {
    if (onActionTaken) {
      onActionTaken({ ...alert, action: 'accepted' });
    }
  };

  const handleDecline = (alert) => {
    if (onActionTaken) {
      onActionTaken({ ...alert, action: 'declined' });
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-sky-500" />
            Predictive Nudges
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            AI-generated recommendations sorted by urgency
          </p>
        </div>
        <span className="badge badge-info">{sortedAlerts.length} active</span>
      </div>

      <div className="space-y-4">
        {sortedAlerts.map((alert, index) => {
          const styles = getUrgencyStyles(alert.urgency);
          
          return (
            <div
              key={`${alert.unit_id}-${index}`}
              className={`p-4 bg-white rounded-lg border border-slate-200 ${styles.border} transition-shadow hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full bg-slate-50 ${styles.icon}`}>
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">Unit {alert.unit_id}</span>
                      <span className={`text-lg font-bold ${getRiskColor(alert.avg_score)}`}>
                        {alert.avg_score}
                      </span>
                    </div>
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${styles.badge}`}>
                      {alert.risk_level}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-slate-700 mb-4 leading-relaxed">
                {alert.recommendation}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Generated {new Date(alert.generated_at).toLocaleTimeString()}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDecline(alert)}
                    className="px-3 py-1.5 text-sm text-slate-600 bg-slate-100 rounded-md hover:bg-slate-200 transition-colors"
                  >
                    Dismiss
                  </button>
                  <button
                    onClick={() => handleAccept(alert)}
                    className="px-3 py-1.5 text-sm text-white bg-sky-500 rounded-md hover:bg-sky-600 transition-colors flex items-center gap-1"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Accept
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {sortedAlerts.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No active nudges. All units within acceptable risk thresholds.</p>
        </div>
      )}
    </div>
  );
};

export default PredictiveNudge;
