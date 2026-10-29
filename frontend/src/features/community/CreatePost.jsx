import { useState } from 'react'
import { api } from '../../api/client'

export default function CreatePost({ onCreated }) {
    const [content, setContent] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleSubmit(event) {
        event.preventDefault()

        // Trims surrounding whitespaces while allowing for leading paragraph indentations
        const trimmedContent = content.replace(/^[ \b\f\n\r]+/, '').replace(/[ \b\f\n\r\t]+$/, '')
        if (!trimmedContent) {
            setError('Post content cannot be empty.')
            return
        }

        setError('')
        setLoading(true)

        try {
            const post = await api.post('/community/posts', {
                content: trimmedContent
            })

            setContent('')
            onCreated(post)
        } catch (requestError) {
            setError(requestError.message || 'Unable to publish your post.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="panel">
            <h2>Share with the community</h2>

            <form onSubmit={handleSubmit}>
                <label htmlFor="post-content">What's on your mind?</label>
                <textarea
                    id="post-content"
                    value={content}
                    onChange={event => setContent(event.target.value)}

                    //  Override default browser Tab key behavior to facilitate paragraph indentations
                    //  TODO: Functionality currently breaks Ctrl+Z (undo)/Ctrl+Y (redo) behavior. Find a way to fix.
                    onKeyDown={event => {
                        if (event.key === 'Tab') {
                            event.preventDefault()

                            const textarea = event.currentTarget
                            const start = textarea.selectionStart
                            const end = textarea.selectionEnd

                            if (event.shiftKey) { // Delete preceding tab if one exists and Shift is held
                                if (start > 0 && content[start - 1] === '\t' && start === end) {
                                    textarea.setRangeText('', start - 1, start, 'end')
                                    setContent(textarea.value)
                                }
                            } else { // Insert tab character
                                textarea.setRangeText('\t', start, end, 'end')
                                setContent(textarea.value)
                            }
                        }
                    }}

                    maxLength={5000}
                    rows={5}
                    placeholder="Write a post to the UF community..."
                    required
                />

                <p className="hint">
                    {content.length}/5000 characters
                </p>

                {error && <p className="error" role="alert">{error}</p>}

                <button type="submit" disabled={loading}>
                    {loading ? 'Publishing...' : 'Publish post'}
                </button>
            </form>
        </section>
    )
}