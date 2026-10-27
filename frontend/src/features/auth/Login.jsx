import { useState } from 'react'

import { api } from '../../api/client'


export default function Login({ onAuthenticated }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await api.post('/auth/login', form)
      onAuthenticated?.(result.user)
    } catch (requestError) {
      setError(requestError.message || 'Unable to log in.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>Log in to SwampSpace</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="login-email">UF email</label>
        <input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={updateField}
          required
        />

        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={updateField}
          required
        />

        {error && <p role="alert">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p>
        Need an account? <a href="/register">Register</a>
      </p>
    </main>
  )
}
