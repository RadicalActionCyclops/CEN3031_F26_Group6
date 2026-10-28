import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function MemberSearch() {
  const [form, setForm] = useState({ q: '', major: '', graduation_year: '' })
  const [search, setSearch] = useState({ q: '', major: '', graduation_year: '', offset: 0 })
  const [state, setState] = useState({ loading: true })
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true
    setState({ loading: true })
    const params = new URLSearchParams({ limit: 20, offset: search.offset })
    for (const key of ['q', 'major', 'graduation_year']) if (search[key]) params.set(key, search[key])
    api.get(`/profiles?${params}`)
      .then(data => { if (active) setState({ data }) })
      .catch(error => { if (active) setState({ error }) })
    return () => { active = false }
  }, [search, retry])
  function submit(event) {
    event.preventDefault()
    setSearch({ q: form.q.trim(), major: form.major.trim(), graduation_year: form.graduation_year, offset: 0 })
  }
  function reset() {
    const empty = { q: '', major: '', graduation_year: '' }
    setForm(empty)
    setSearch({ ...empty, offset: 0 })
  }
  return (
    <section>
      <p className="eyebrow">Discover your community</p><h1>Find UF members</h1>
      <p>Search names and majors, or narrow your search with filters.</p>
      <form className="panel search-form" onSubmit={submit}>
        <div><label htmlFor="keyword">Name or major</label><input id="keyword" maxLength={200} value={form.q} onChange={e => setForm({ ...form, q: e.target.value })} placeholder="Search members" /></div>
        <div><label htmlFor="filter-major">Exact major or degree</label><input id="filter-major" maxLength={120} value={form.major} onChange={e => setForm({ ...form, major: e.target.value })} /></div>
        <div><label htmlFor="filter-year">Graduation year</label><input id="filter-year" type="number" min="1900" max="2100" step="1" value={form.graduation_year} onChange={e => setForm({ ...form, graduation_year: e.target.value })} /></div>
        <div className="actions"><button type="submit">Search</button><button className="secondary" type="button" onClick={reset}>Clear</button></div>
      </form>
      {state.loading && <p role="status">Finding members…</p>}
      {state.error && <div role="alert"><p>{state.error.message}</p><button onClick={() => setRetry(retry + 1)}>Try again</button></div>}
      {state.data && <>
        <p role="status">{state.data.total} {state.data.total === 1 ? 'member' : 'members'} found</p>
        {state.data.total === 0 && <div className="panel"><h2>No members match your search</h2><p>Try a different keyword or clear your filters.</p></div>}
        <div className="member-grid">{state.data.items.map(member => (
          <article className="panel member-card" key={member.user_id}>
            <span className="badge">{member.status === 'student' ? 'Student' : 'Alumni'}</span>
            <h2><a href={`/profiles/${member.user_id}`}>{member.full_name}</a></h2>
            <p>{member.major || 'Major not provided'}</p><p>Class of {member.graduation_year}</p>
            {member.title && <p>{member.title}</p>}
          </article>
        ))}</div>
        {state.data.total > 20 && <div className="actions pagination">
          <button disabled={search.offset === 0} onClick={() => setSearch({ ...search, offset: search.offset - 20 })}>Previous</button>
          <span>Page {Math.floor(search.offset / 20) + 1} of {Math.ceil(state.data.total / 20)}</span>
          <button disabled={search.offset + 20 >= state.data.total} onClick={() => setSearch({ ...search, offset: search.offset + 20 })}>Next</button>
        </div>}
      </>}
    </section>
  )
}
