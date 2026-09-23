export const CATEGORIES = [
  'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
  'Health & Medical', 'Housing', 'Utilities', 'Travel', 'Education', 'Other',
]

export const CATEGORY_COLORS = {
  'Food & Dining': 'bg-orange-100 text-orange-700',
  'Transportation': 'bg-blue-100 text-blue-700',
  'Shopping': 'bg-pink-100 text-pink-700',
  'Entertainment': 'bg-purple-100 text-purple-700',
  'Health & Medical': 'bg-red-100 text-red-700',
  'Housing': 'bg-yellow-100 text-yellow-700',
  'Utilities': 'bg-cyan-100 text-cyan-700',
  'Travel': 'bg-indigo-100 text-indigo-700',
  'Education': 'bg-green-100 text-green-700',
  'Other': 'bg-gray-100 text-gray-600',
}

export const inputCls =
  'border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500'

export const money = (n) =>
  n.toLocaleString('en-CA', { style: 'currency', currency: 'CAD' })

export const CHART_BLUE = '#2a78d6'
