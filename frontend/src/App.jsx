import { useEffect, useState } from 'react'

import Login from './features/auth/Login'
import Register from './features/auth/Register'
import { api } from './api/client'
import Profile from './features/profiles/Profile'
import EditProfile from './features/profiles/EditProfile'
import MemberSearch from './features/profiles/MemberSearch'
import Inbox from './features/messages/Inbox'
import Chat from './features/messages/Chat'
import Feed from './features/community/Feed'


export default function App() {
    const [authenticatedUser, setAuthenticatedUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [sessionError, setSessionError] = useState('')
    const [editing, setEditing] = useState(false)
    const [editProfile, setEditProfile] = useState(null)
    const [savedProfile, setSavedProfile] = useState(null)

    useEffect(() => {
        let active = true
        api.get('/auth/status').then(result => {
            if (active) setAuthenticatedUser(result.user)
        }).catch(error => {
            if (active) setSessionError(error.message)
        }).finally(() => { if (active) setLoading(false) })
        return () => { active = false }
    }, [])

    async function logout() {
        try {
            await api.post('/auth/logout')
            setAuthenticatedUser(null)
            setEditing(false)
            setSessionError('')
        } catch (error) { setSessionError(error.message) }
    }

    if (window.location.pathname === '/register') {
        return <Register />
    }

    if (loading) return <main><p role="status">Loading SwampSpace…</p></main>

    if (authenticatedUser) {
        return (
            <>
                <header className="site-header">
                    <a className="brand" href="/">SwampSpace</a>
                    <nav aria-label="Main navigation">
                        <a href="/community">Community</a>
                        <a href="/profiles/me">My Profile</a>
                        <a href="/messages">Messages</a>
                        <a href="/members">Find Members</a>
                        <button className="secondary" onClick={logout}>Log out</button>
                    </nav>
                </header>
                <main>
                    {sessionError && <p role="alert" className="error">{sessionError}</p>}
                    {(!authenticatedUser.email_verified || authenticatedUser.account_status !== 'active' || authenticatedUser.affiliation_status !== 'verified') ? (
                        <section className="panel">
                            <h1>Membership verification required</h1>
                            <p>Profiles and member search are available to verified UF community members.</p>
                            <p>{!authenticatedUser.email_verified
                                ? 'Complete email verification first. UF affiliation must also be confirmed by the approved membership process.' :
                                'Your email is verified. UF affiliation verification is still required before you can access member content.'}
                            </p>
                        </section>
                    ) : editing ? (
                            <EditProfile profile={editProfile} user={authenticatedUser} onCancel={() => setEditing(false)} onSaved={profile => {
                                setSavedProfile(profile)
                                setAuthenticatedUser({ ...authenticatedUser, display_name: profile.full_name, affiliation: profile.status })
                                setEditing(false)
                            }} />
                    ) : window.location.pathname === '/community' ? (
                            <Feed userId={authenticatedUser.id} />
                    ) : window.location.pathname === '/messages' ? (
                        <Inbox />
                    ) : window.location.pathname.startsWith('/messages/') ? (
                        <Chat userId={window.location.pathname.split('/')[2]} />
                    ) : window.location.pathname === '/members' ? (
                            <MemberSearch />
                    ) : (
                            <Profile
                                user={authenticatedUser}
                                userId={
                                    window.location.pathname.startsWith('/profiles/')
                                        ? window.location.pathname.split('/')[2] === 'me'
                                            ? null
                                            : window.location.pathname.split('/')[2]
                                        : null
                                }
                                onEdit={profile => {
                                    setEditProfile(profile)
                                    setEditing(true)
                                }}
                                savedProfile={savedProfile}
                            />
                    )}
                </main>
            </>
        )
    }

    return <> {
        sessionError && <p role="alert" className="error">
            {sessionError}
        </p>}<Login onAuthenticated={user => { setAuthenticatedUser(user); setSessionError('') }} /> </>
}
