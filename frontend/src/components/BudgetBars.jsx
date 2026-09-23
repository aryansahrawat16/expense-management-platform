import { CheckCircle2, AlertTriangle, XCircle, Trash2 } from 'lucide-react'
import { STATUS, money } from '../constants'

const ICONS = { ok: CheckCircle2, warning: AlertTriangle, over: XCircle }

export default function BudgetBars({ budgets, onDelete }) {
  return (
    <ul className="space-y-4">
      {budgets.map(b => {
        const s = STATUS[b.status]
        const Icon = ICONS[b.status]
        return (
          <li key={b.id}>
            <div className="flex items-center justify-between gap-3 text-sm mb-1.5">
              <span className="font-medium text-gray-800">{b.category}</span>
              <span className="flex items-center gap-3">
                <span className={`flex items-center gap-1 text-xs font-medium ${s.text}`}>
                  <Icon size={14} aria-hidden="true" /> {s.label}
                </span>
                {onDelete && (
                  <button onClick={() => onDelete(b)} aria-label={`Remove ${b.category} budget`}
                    className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition">
                    <Trash2 size={14} />
                  </button>
                )}
              </span>
            </div>
            <div className="h-2.5 rounded bg-gray-100 overflow-hidden" role="progressbar"
              aria-valuenow={b.percent} aria-valuemin={0} aria-valuemax={100} aria-label={`${b.category} budget used`}>
              <div className="h-full rounded transition-all" style={{ width: `${Math.min(b.percent, 100)}%`, background: s.color }} />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{money(b.spent)} of {money(b.monthly_limit)} ({b.percent}%)</span>
              <span>{b.remaining >= 0 ? `${money(b.remaining)} left` : `${money(-b.remaining)} over`}</span>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
