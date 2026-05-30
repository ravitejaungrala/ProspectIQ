export default function Card({ children, style = {}, onClick, accent = false }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: '#ffffff',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '22px',
        transition: 'var(--transition)',
        boxShadow: 'var(--shadow-sm)',
        position: 'relative',
        overflow: 'hidden',
        ...(onClick ? { cursor: 'pointer' } : {}),
        ...style,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = 'var(--shadow-md)'
        e.currentTarget.style.borderColor = 'var(--border-hover)'
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-2px)'
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      {/* Top gradient accent bar on every card */}
      <span style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: '3px',
        background: 'linear-gradient(90deg, #ff4500, #10b981)',
        opacity: accent ? 1 : 0.45,
        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
        pointerEvents: 'none',
      }} />
      {children}
    </div>
  )
}
