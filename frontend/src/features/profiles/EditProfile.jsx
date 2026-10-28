import { useState } from 'react'
import { api } from '../../api/client'

export default function EditProfile({ profile, user, onSaved, onCancel }) {
  const [form, setForm] = useState({
    full_name: profile?.full_name ?? user.display_name,
    status: profile?.status ?? user.affiliation,
    graduation_year: profile?.graduation_year ?? '',
    major: profile?.major ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  function change(event) {
    setForm({ ...form, [event.target.name]: event.target.value })
  }
  async function submit(event) {
    event.preventDefault()
    if (form.full_name.trim().length < 2) {
      setError('Enter your full name using at least two characters.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const save = profile ? api.patch : api.post
      const result = await save('/profiles/me', {
        ...form, graduation_year: Number(form.graduation_year),
      })
      onSaved(result)
    } catch (err) {
      setError(err.message || 'Unable to save your profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Your place in the Gator community</p>
      <h1>{profile ? 'Edit your profile' : 'Create your profile'}</h1>
      <p>Share your academic background so other members can find you. Fields marked * are required.</p>
      <form onSubmit={submit}>
        <fieldset disabled={saving}>
          <label htmlFor="full-name">Full name *</label>
          <input id="full-name" name="full_name" autoComplete="name" value={form.full_name} onChange={change} minLength={2} maxLength={100} required />
          <label htmlFor="status">UF status *</label>
          <select id="status" name="status" value={form.status} onChange={change} required>
            <option value="">Select your status</option>
            <option value="student">Student</option><option value="alumni">Alumni</option>
          </select>
          <p className="hint">Your profile status describes you; it does not change membership verification.</p>
          <label htmlFor="graduation-year">Graduation year *</label>
          <input id="graduation-year" name="graduation_year" type="number" min="1900" max={new Date().getFullYear() + 10} step="1" value={form.graduation_year} onChange={change} required />
          <label htmlFor="major">Major or degree</label>
          <input id="major" name="major" value={form.major} onChange={change} maxLength={120} placeholder="e.g. Computer Science" />
          {error && <p role="alert" className="error">{error}</p>}
          <div className="actions">
            <button type="submit">{saving ? 'Saving…' : 'Save profile'}</button>
            <button className="secondary" type="button" onClick={onCancel}>Cancel</button>
          </div>
        </fieldset>
      </form>
    </section>
  )
}
