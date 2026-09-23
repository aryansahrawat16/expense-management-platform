import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { CHART_BLUE, money } from '../constants'

const monthLabel = (ym) => {
  const [y, m] = ym.split('-').map(Number)
  return new Date(y, m - 1).toLocaleString('en-CA', { month: 'short' })
}

function describeChange(c) {
  if (c.last_month === 0) return { text: `new this month (${money(c.this_month)})`, up: true }
  if (c.this_month === 0) return { text: `none yet this month (was ${money(c.last_month)})`, up: false }
  const up = c.change_pct > 0
  return { text: `${up ? 'up' : 'down'} ${Math.abs(c.change_pct)}% (${money(c.this_month)} vs ${money(c.last_month)})`, up }
}

export default function TrendsPanel({ trends }) {
  const data = trends.months.map(m => ({ ...m, label: monthLabel(m.month) }))
  const up = trends.change_pct !== null && trends.change_pct > 0

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="font-semibold text-gray-800">Spending Trends</h2>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
        <div>
          <p className="text-xs text-gray-500">This month</p>
          <p className="text-xl font-bold text-gray-900">{money(trends.this_month_total)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">vs last month ({money(trends.last_month_total)})</p>
          {trends.change_pct === null ? (
            <p className="text-sm text-gray-500 mt-1">No spending last month</p>
          ) : (
            <p className={`flex items-center gap-1 text-xl font-bold ${up ? 'text-red-700' : 'text-green-700'}`}>
              {up ? <TrendingUp size={18} aria-hidden="true" /> : <TrendingDown size={18} aria-hidden="true" />}
              {up ? '+' : ''}{trends.change_pct}%
            </p>
          )}
        </div>
        <div>
          <p className="text-xs text-gray-500">On pace for</p>
          <p className="text-xl font-bold text-gray-900">{money(trends.projected_month_total)}</p>
        </div>
      </div>

      <div className="mt-4" aria-label="Monthly spending over the last six months">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#eceae6" />
            <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#52514e' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#52514e' }} axisLine={false} tickLine={false} width={56}
              tickFormatter={(v) => `$${v}`} />
            <Tooltip formatter={(v) => [money(v), 'Spent']} cursor={{ stroke: '#b5b3ad', strokeWidth: 1 }} />
            <Line type="monotone" dataKey="total" stroke={CHART_BLUE} strokeWidth={2}
              dot={{ r: 4, fill: CHART_BLUE, stroke: '#fff', strokeWidth: 2 }} activeDot={{ r: 5 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {trends.categories.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Biggest changes vs last month</h3>
          <ul className="space-y-1.5">
            {trends.categories.slice(0, 3).map(c => {
              const d = describeChange(c)
              return (
                <li key={c.category} className="flex items-center gap-2 text-sm">
                  {d.up
                    ? <TrendingUp size={15} className="text-red-700 shrink-0" aria-label="increase" />
                    : <TrendingDown size={15} className="text-green-700 shrink-0" aria-label="decrease" />}
                  <span className="font-medium text-gray-800">{c.category}</span>
                  <span className="text-gray-500">{d.text}</span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
