import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function Profile({ user, userId, onEdit, savedProfile }) {
  const [state, setState] = useState({ loading: true })
  
  // This variable determines if the user is looking at their own profile
  const own = !userId || userId === user.id
  
  useEffect(() => {
    let active = true
    setState({ loading: true })
    api.get(`/profiles/${own ? 'me' : encodeURIComponent(userId)}`)
      .then(profile => { if (active) setState({ profile }) })
      .catch(error => { if (active) setState({ error }) })
    return () => { active = false }
  }, [userId, own, savedProfile])
  
  if (state.loading) return <p role="status">Loading profile…</p>
  
  if (state.error) return (
    <section className="panel">
      <h1>{state.error.status === 404 ? (own ? 'Introduce yourself' : 'Profile not found') : 'Unable to load profile'}</h1>
      <p>{state.error.status === 404 ? (own ? 'Create your profile to help UF students and alumni discover you.' : 'This member has no available profile.') : state.error.message}</p>
      {own && state.error.status === 404 && <button onClick={() => onEdit(null)}>Create profile</button>}
      <p><a href="/members">Find members</a></p>
    </section>
  )
  
  const { profile } = state
  
  return (
    <section className="panel profile">
      <p className="eyebrow">UF community member</p>
      <div className="avatar" aria-hidden="true">{profile.full_name.split(' ').map(n => n[0]).slice(0, 2).join('')}</div>
      <h1>{profile.full_name}</h1>
      <p className="badge">{profile.status === 'student' ? 'Student' : 'Alumni'}</p>
      <dl><dt>Major or degree</dt><dd>{profile.major || 'Not provided'}</dd><dt>Graduation year</dt><dd>{profile.graduation_year}</dd></dl>
      {savedProfile?.user_id === profile.user_id && <p role="status" className="success">Your profile was saved.</p>}
      <div className="actions">
        {own && <button onClick={() => onEdit(profile)}>Edit profile</button>}
        
        {/* ADDED: Only shows the Message button if it is NOT their own profile */}
        {!own && <button onClick={() => window.location.assign(`/messages/${profile.user_id}`)}>Message</button>}
        
        <a href="/members">Explore members</a>
      </div>
    </section>
  )
}