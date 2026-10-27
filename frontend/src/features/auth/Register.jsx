import { useState } from 'react'

import { api } from '../../api/client'


const initialForm = {
  displayName: '',
  email: '',
  password: '',
  confirmPassword: '',
}

export default function Register() {
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState('')

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  function validate() {
    if (!form.email.toLowerCase().endsWith('@ufl.edu')) {
      return 'Use your @ufl.edu email address.'
    }
    if (form.password.length < 12) {
      return 'Password must be at least 12 characters.'
    }
    if (form.password !== form.confirmPassword) {
      return 'Passwords do not match.'
    }
    return ''
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setError('')
    setLoading(true)
    try {
      await api.post('/auth/register', {
        display_name: form.displayName,
        email: form.email,
        password: form.password,
      })
      setRegisteredEmail(form.email)
      setForm(initialForm)
    } catch (requestError) {
      setError(requestError.message || 'Unable to create the account.')
    } finally {
      setLoading(false)
    }
  }

  if (registeredEmail) {
    return (
      <main>
        <h1>Check the development email outbox</h1>
        <p>
          Registration succeeded for {registeredEmail}. Use the verification token
          written by the backend&apos;s configured development email adapter.
        </p>
        <p>
          Email verification confirms ownership only. UF community eligibility
          requires a separately approved affiliation check.
        </p>
        <a href="/">Continue to login</a>
      </main>
    )
  }

  return (
    <main>
      <h1>Create a SwampSpace account</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="register-name">Display name</label>
        <input
          id="register-name"
          name="displayName"
          type="text"
          autoComplete="name"
          minLength="2"
          maxLength="100"
          value={form.displayName}
          onChange={updateField}
          required
        />

        <label htmlFor="register-email">UF email</label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={updateField}
          required
        />

        <label htmlFor="register-password">Password</label>
        <input
          id="register-password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength="12"
          maxLength="128"
          value={form.password}
          onChange={updateField}
          required
        />

        <label htmlFor="register-confirm-password">Confirm password</label>
        <input
          id="register-confirm-password"
          name="confirmPassword"
          type="password"
          autoComplete="new-password"
          value={form.confirmPassword}
          onChange={updateField}
          required
        />

        {error && <p role="alert">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Creating account…' : 'Register'}
        </button>
      </form>
      <p>
        Already registered? <a href="/">Log in</a>
      </p>
    </main>
  )
}
