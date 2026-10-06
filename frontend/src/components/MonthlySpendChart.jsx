// Categories cycle through these; an explicit `color` on a data item (e.g. the
// Income slice) always wins, so Income can stay visually distinct from expenses.
const EXPENSE_COLORS = ['#B4501E', '#3B5BA5', '#8E2A2A', '#2E8B87', '#C9A227', '#6B4C9A', '#4C7A3B', '#9C5B3D']

export default function MonthlySpendChart({ data, centerLabel = 'Total', centerValue }) {
  if (!data || data.length === 0) {
    return <p className="empty">No expenses recorded for this period yet.</p>
  }

  const total = data.reduce((sum, d) => sum + d.total, 0)
  const displayValue = centerValue !== undefined && centerValue !== null ? centerValue : total
  const size = 180
  const strokeWidth = 28
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  let cumulative = 0
  let colorIndex = 0
  const segments = data.map((d) => {
    const fraction = total > 0 ? d.total / total : 0
    const dash = fraction * circumference
    const dashOffset = -cumulative
    cumulative += dash
    const color = d.color || EXPENSE_COLORS[colorIndex++ % EXPENSE_COLORS.length]
    return { ...d, color, dash, dashOffset, percent: fraction * 100 }
  })

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="donut-chart">
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="var(--surface-2)" strokeWidth={strokeWidth}
          />
          {segments.map((s, i) => (
            <circle
              key={s.category_id ?? i}
              cx={size / 2} cy={size / 2} r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth={strokeWidth}
              strokeDasharray={`${s.dash} ${circumference}`}
              strokeDashoffset={s.dashOffset}
              strokeLinecap="butt"
            />
          ))}
        </g>
        <text x="50%" y="46%" textAnchor="middle" className="donut-total-label">{centerLabel}</text>
        <text x="50%" y="60%" textAnchor="middle" className="donut-total-value">£{displayValue.toFixed(0)}</text>
      </svg>
      <ul className="donut-legend">
        {segments.map((s, i) => (
          <li key={s.category_id ?? i}>
            <span className="swatch" style={{ background: s.color }} />
            <span className="legend-name">{s.category_name || 'Uncategorised'}</span>
            <span className="legend-value">
              £{s.total.toFixed(0)} <span className="legend-percent">({s.percent.toFixed(0)}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
