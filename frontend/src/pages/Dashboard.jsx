import { useEffect, useRef, useState } from 'react'
import {
  listCategories, createCategory,
  listTransactions, createTransaction, deleteTransaction,
  rangeSummary,
} from '../api.js'
import MonthlySpendChart from '../components/MonthlySpendChart.jsx'

const RANGE_OPTIONS = [
  { value: 'week', label: 'Last week' },
  { value: 'month', label: 'Last month' },
  { value: '3months', label: 'Last 3 months' },
  { value: '3years', label: 'Last 3 years' },
]

const TX_FILTERS = [
  { value: 'latest5', label: 'Latest 5' },
  { value: 'latest10', label: 'Latest 10' },
  { value: 'today', label: 'Today' },
  { value: '10days', label: 'Last 10 days' },
  { value: '30days', label: 'Last 30 days' },
  { value: 'all', label: 'All transactions' },
]

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
  } catch {
    return iso
  }
}

function filterTransactions(transactions, filter) {
  // `transactions` is already sorted newest-first by the API.
  if (filter === 'all') return transactions
  if (filter === 'latest5') return transactions.slice(0, 5)
  if (filter === 'latest10') return transactions.slice(0, 10)

  const now = new Date()
  let cutoff
  if (filter === 'today') {
    cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  } else if (filter === '10days') {
    cutoff = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000)
  } else if (filter === '30days') {
    cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  } else {
    return transactions.slice(0, 10)
  }
  return transactions.filter((tx) => new Date(tx.date) >= cutoff)
}

export default function Dashboard({ onLogout }) {
  const [categories, setCategories] = useState([])
  const [transactions, setTransactions] = useState([])
  const [summary, setSummary] = useState(null)
  const [range, setRange] = useState('month')
  const [txFilter, setTxFilter] = useState('latest5')
  const [txMenuOpen, setTxMenuOpen] = useState(false)
  const [error, setError] = useState('')

  const [newCategoryName, setNewCategoryName] = useState('')
  const [form, setForm] = useState({ amount: '', type: 'expense', description: '', category_id: '' })

  const txMenuRef = useRef(null)

  const categoryName = (id) => categories.find((c) => c.id === id)?.name
  const rangeLabel = RANGE_OPTIONS.find((r) => r.value === range)?.label ?? range
  const txFilterLabel = TX_FILTERS.find((f) => f.value === txFilter)?.label ?? 'Transactions'
  const visibleTransactions = filterTransactions(transactions, txFilter)

  async function refresh() {
    try {
      const [cats, txs, sum] = await Promise.all([
        listCategories(), listTransactions(), rangeSummary(range),
      ])
      setCategories(cats)
      setTransactions(txs)
      setSummary(sum)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { refresh() }, [range])

  useEffect(() => {
    function handleClickOutside(e) {
      if (txMenuRef.current && !txMenuRef.current.contains(e.target)) {
        setTxMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function handleAddCategory(e) {
    e.preventDefault()
    if (!newCategoryName.trim()) return
    try {
      await createCategory(newCategoryName.trim())
      setNewCategoryName('')
      refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleAddTransaction(e) {
    e.preventDefault()
    try {
      await createTransaction({
        amount: parseFloat(form.amount),
        type: form.type,
        description: form.description || null,
        category_id: form.category_id ? parseInt(form.category_id, 10) : null,
      })
      setForm({ amount: '', type: 'expense', description: '', category_id: '' })
      refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteTransaction(id)
      refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="dashboard">
      <header>
        <h1>myAccountant</h1>
        <button className="ghost" onClick={onLogout}>Log out</button>
      </header>

      {error && <p className="error">{error}</p>}

      <div className="range-selector">
        {RANGE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            className={opt.value === range ? 'range-btn active' : 'range-btn'}
            onClick={() => setRange(opt.value)}
            type="button"
          >
            {opt.label}
          </button>
        ))}
      </div>

      {summary && (
        <section className="summary-cards">
          <div className="card">
            <span className="label">Income &middot; {rangeLabel}</span>
            <span className="value positive">£{summary.total_income.toFixed(2)}</span>
          </div>
          <div className="card">
            <span className="label">Expense</span>
            <span className="value negative">£{summary.total_expense.toFixed(2)}</span>
          </div>
          <div className="card">
            <span className="label">Net</span>
            <span className={`value ${summary.net >= 0 ? 'positive' : 'negative'}`}>£{summary.net.toFixed(2)}</span>
          </div>
        </section>
      )}

      <section>
        <h2>Spend by category &middot; {rangeLabel.toLowerCase()}</h2>
        <div className="chart-card">
          <MonthlySpendChart
            data={summary?.category_breakdown ?? []}
            centerLabel="Net"
            centerValue={summary?.net}
          />
        </div>
      </section>

      <section className="two-col">
        <div>
          <h2>Add category</h2>
          <form onSubmit={handleAddCategory} className="inline-form">
            <input
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="e.g. Groceries"
            />
            <button type="submit">Add</button>
          </form>

          <h2>Add transaction</h2>
          <form onSubmit={handleAddTransaction} className="stacked-form">
            <div className="form-row">
              <label>
                Amount
                <input
                  type="number" step="0.01" required
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
              </label>
              <label>
                Type
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </label>
            </div>
            <label>
              Category
              <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                <option value="">None</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </label>
            <label>
              Description
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Optional"
              />
            </label>
            <button type="submit">Add transaction</button>
          </form>
        </div>

        <div>
          <div className="tx-menu-wrap" ref={txMenuRef}>
            <button className="tx-menu-btn" type="button" onClick={() => setTxMenuOpen((o) => !o)}>
              Transactions <span className="tx-menu-sub">&middot; {txFilterLabel}</span>
              <span className="caret">{txMenuOpen ? '▴' : '▾'}</span>
            </button>
            {txMenuOpen && (
              <ul className="tx-menu">
                {TX_FILTERS.map((f) => (
                  <li key={f.value}>
                    <button
                      type="button"
                      className={f.value === txFilter ? 'active' : ''}
                      onClick={() => { setTxFilter(f.value); setTxMenuOpen(false) }}
                    >
                      {f.label}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <ul className="tx-list">
            {visibleTransactions.map((tx) => (
              <li key={tx.id} className={tx.type}>
                <span className="tx-dot" />
                <span className="tx-main">
                  <span className="tx-desc">
                    {tx.description
                      || categoryName(tx.category_id)
                      || (tx.type === 'income' ? 'Income' : 'Expense')}
                  </span>
                  <span className="tx-meta">
                    <span>{formatDate(tx.date)}</span>
                    {tx.description && tx.category_id && (
                      <span className="tx-category">{categoryName(tx.category_id) || 'Uncategorised'}</span>
                    )}
                  </span>
                </span>
                <span className="tx-amount">{tx.type === 'expense' ? '-' : '+'}£{tx.amount.toFixed(2)}</span>
                <button className="icon-btn" onClick={() => handleDelete(tx.id)} aria-label="Delete transaction">
                  &times;
                </button>
              </li>
            ))}
            {visibleTransactions.length === 0 && <li className="empty">No transactions in this range.</li>}
          </ul>
        </div>
      </section>
    </div>
  )
}
