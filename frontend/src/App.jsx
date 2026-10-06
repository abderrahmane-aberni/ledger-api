import { useState } from 'react'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import { isLoggedIn, logout } from './api.js'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn())

  function handleLogout() {
    logout()
    setLoggedIn(false)
  }

  if (!loggedIn) {
    return <Login onLoggedIn={() => setLoggedIn(true)} />
  }

  return <Dashboard onLogout={handleLogout} />
}
