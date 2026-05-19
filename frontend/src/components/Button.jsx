export default function Button({ children, onClick, variant = 'primary', size = 'md', disabled = false, style = {} }) {
  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    border: 'none',
    borderRadius: '8px',
    fontWeight: 600,
    transition: 'all 0.15s',
    opacity: disabled ? 0.5 : 1,
    pointerEvents: disabled ? 'none' : 'auto',
    ...sizeStyles[size],
    ...variantStyles[variant],
    ...style,
  }

  return (
    <button onClick={onClick} disabled={disabled} style={baseStyle}>
      {children}
    </button>
  )
}

const sizeStyles = {
  sm: { padding: '6px 14px', fontSize: '12px' },
  md: { padding: '10px 20px', fontSize: '14px' },
  lg: { padding: '12px 28px', fontSize: '15px' },
}

const variantStyles = {
  primary: {
    background: '#ff4500',
    color: '#fff',
  },
  secondary: {
    background: '#ffffff',
    color: '#1a1a1a',
    border: '1px solid #e0e0e0',
  },
  success: {
    background: 'rgba(22, 163, 74, 0.12)',
    color: '#16a34a',
  },
  danger: {
    background: 'rgba(220, 38, 38, 0.12)',
    color: '#dc2626',
  },
  ghost: {
    background: 'transparent',
    color: '#555555',
  },
}
