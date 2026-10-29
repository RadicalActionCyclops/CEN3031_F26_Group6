import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import CreatePost from './CreatePost'

export default function Feed({ userId }) {
    const [posts, setPosts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [editingPostId, setEditingPostId] = useState(null)
    const [editedContent, setEditedContent] = useState('')
    const [editError, setEditError] = useState('')
    const [savingEdit, setSavingEdit] = useState(false)
    const [deletingPostId, setDeletingPostId] = useState(null)

    const loadPosts = useCallback(async () => {
        setError('')
        try {
            const data = await api.get('/community/posts')
            setPosts(data)
        } catch (requestError) {
            setError(requestError.message || 'Unable to load community posts.')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        loadPosts()
    }, [loadPosts])

    function handleCreated(post) {
        setPosts(currentPosts => [post, ...currentPosts])
    }

    function handleEdit(post) {
        setEditingPostId(post.id)
        setEditedContent(post.content)
    }

    function handleCancelEdit() {
        setEditingPostId(null)
        setEditedContent('')
    }

    async function handleSave(postId) {
        const originalPost = posts.find(post => post.id === postId)
        // Trim surrounding whitespace, except for leading tabs
        const trimmedContent = editedContent
            .replace(/^[ \b\f\n\r]+/, '')
            .replace(/[ \b\f\n\r\t]+$/, '')

        if (!trimmedContent) {
            setError('Post cannot be empty.')
            return
        } else if (!originalPost || trimmedContent === originalPost.content
            .replace(/^[ \b\f\n\r]+/, '')
            .replace(/[ \b\f\n\r\t]+$/, ''))
            return

        setSavingEdit(true)

        try {
            const updatedPost = await api.patch(
                `/community/posts/${postId}`,
                { content: trimmedContent }
            )

            setPosts(currentPosts =>
                currentPosts.map(post =>
                    post.id === postId ? updatedPost : post
                )
            )

            handleCancelEdit()
            setError('')
        } catch (requestError) {
            setError(requestError.message || 'Unable to update post.')
        } finally {
            setSavingEdit(false)
        }
    }

    async function handleDelete(postId) {
        if (!window.confirm('Are you sure you want to delete this post?'))
            return

        setDeletingPostId(postId)

        try {
            await api.delete(`/community/posts/${postId}`)

            setPosts(currentPosts =>
                currentPosts.filter(post => post.id !== postId)
            )

            setError('')
        } catch (requestError) {
            setError(requestError.message || 'Unable to delete post.')
        } finally {
            setDeletingPostId(null)
        }
    }

    return (
        <div className="community-feed">
            <CreatePost onCreated={handleCreated} />

            <section className="panel">
                <h2>Community Feed</h2>

                {loading && <p>Loading posts...</p>}

                {error && (
                    <p className="error" role="alert">{error}</p>
                )}

                {!loading && !error && posts.length === 0 && (
                    <p className="hint">
                        No posts yet. Be the first to share something!
                    </p>
                )}

                {posts.map(post => (
                    <article className="community-post" key={post.id}>
                        <h3>{post.author_name}</h3>
                        <p className="hint">
                            {/* TODO: Backend currently does not return timezone information,
                                despite API calls specifying UTC.
                                Until a proper fix can be made, timestamps are appended with 'Z'.
                                This ensures the browser knows to convert to local time. */}
                            Posted at {new Date(post.created_at + 'Z').toLocaleString()}
                            {new Date(post.updated_at + 'Z').getTime() !== new Date(post.created_at + 'Z').getTime() && (
                                <> (Edited at {new Date(post.updated_at + 'Z').toLocaleString()})</>
                            )}
                        </p>

                        {editingPostId === post.id ? (
                            <textarea
                                value={editedContent}
                                onChange={event => setEditedContent(event.target.value)}

                                //  Override default browser Tab key behavior to facilitate paragraph indentations
                                //  TODO: Functionality currently breaks Ctrl+Z (undo)/Ctrl+Y (redo) behavior. Find a way to fix.
                                onKeyDown={event => {
                                    if (event.key === 'Tab') {
                                        event.preventDefault()

                                        const textarea = event.currentTarget
                                        const start = textarea.selectionStart
                                        const end = textarea.selectionEnd

                                        if (event.shiftKey) { // Delete preceding tab if one exists on Shift+Tab press
                                            if (start > 0 && editedContent[start - 1] === '\t' && start === end) {
                                                textarea.setRangeText('', start - 1, start, 'end')
                                                setEditedContent(textarea.value)
                                            }
                                        } else { // Insert tab character on Tab press
                                            textarea.setRangeText('\t', start, end, 'end')
                                            setEditedContent(textarea.value)
                                        }
                                    }
                                }}

                                maxLength={5000}
                                rows={5}
                            />
                        ) : (
                                <p className="post-content">{post.content}</p>
                        )}

                        {post.user_id === userId && (
                            <div>
                                {editingPostId === post.id ? (
                                    <>
                                        <button
                                            type="button"
                                            onClick={() => handleSave(post.id)}
                                            disabled={savingEdit || editedContent
                                                .replace(/^[ \b\f\n\r]+/, '')
                                                .replace(/[ \b\f\n\r\t]+$/, '')
                                                === post.content
                                                    .replace(/^[ \b\f\n\r]+/, '')
                                                    .replace(/[ \b\f\n\r\t]+$/, '')}
                                        >
                                            {savingEdit ? 'Saving...' : 'Save'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleCancelEdit}
                                        >
                                            Cancel
                                        </button>
                                    </>
                                ) : (
                                        <>
                                            <button
                                                type="button"
                                                onClick={() => handleEdit(post)}
                                            >
                                                Edit
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleDelete(post.id)}
                                                disabled={deletingPostId === post.id}
                                            >
                                                {deletingPostId === post.id ? 'Deleting...' : 'Delete'}
                                            </button>
                                        </>
                                )}
                            </div>
                        )}
                    </article>
                ))}
            </section>
        </div>
    )
}