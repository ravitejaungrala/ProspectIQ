import Sidebar from './Sidebar'

export default function Layout({ children }) {
  return (
    <div style={styles.container}>
      <Sidebar />
      <main style={styles.main}>
        {children}
      </main>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    background: 'var(--bg-secondary)',
  },
  main: {
    flex: 1,
    marginLeft: 'var(--sidebar-width)',
    padding: '32px 36px',
    maxWidth: 'calc(100vw - var(--sidebar-width))',
    minHeight: '100vh',
  },
}
