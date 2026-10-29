import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';

export default function Inbox() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInbox();
  }, []);

  const fetchInbox = async () => {
    try {
      const response = await api.get('/messages/inbox');
      // Set directly to response, omitting .data to prevent white screens
      setConversations(response);
    } catch (error) {
      console.error("Error fetching inbox:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <main><p role="status">Loading messages...</p></main>;

  return (
    <section className="panel inbox-container">
      <h2>Direct Messages</h2>
      {(!conversations || conversations.length === 0) ? (
        <p>No conversations yet. Search for members to start networking!</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {conversations.map((conv) => (
            <div 
              key={conv.user_id} 
              onClick={() => window.location.assign(`/messages/${conv.user_id}`)}
              style={{ 
                cursor: 'pointer', 
                padding: '15px', 
                border: '1px solid #ccc', 
                borderRadius: '8px',
                backgroundColor: conv.unread_count > 0 ? '#f0f8ff' : '#fff'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <strong style={{ fontSize: '1.1rem' }}>{conv.username}</strong>
                <span style={{ fontSize: '0.85rem', color: '#666' }}>
                  {new Date(conv.timestamp.endsWith('Z') ? conv.timestamp : conv.timestamp + 'Z').toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#444' }}>
                <span>{conv.last_message}</span>
                {conv.unread_count > 0 && (
                  <span style={{ 
                    backgroundColor: '#00529b', 
                    color: 'white', 
                    padding: '2px 8px', 
                    borderRadius: '12px', 
                    fontSize: '0.85rem' 
                  }}>
                    {conv.unread_count} new
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}