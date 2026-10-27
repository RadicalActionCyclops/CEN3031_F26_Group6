import { useState } from 'react'

import Login from './features/auth/Login'
import Register from './features/auth/Register'


export default function App() {
  const [authenticatedUser, setAuthenticatedUser] = useState(null)

  if (window.location.pathname === '/register') {
    return <Register />
  }

  if (authenticatedUser) {
    return (
      <main>
        <h1>Welcome, {authenticatedUser.display_name}</h1>
        <p>Your local development session is active.</p>
      </main>
    )
  }

  return <Login onAuthenticated={setAuthenticatedUser} />
}
