import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';

export default function Chat({ userId }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [currentUserId, setCurrentUserId] = useState(null);
  const [otherUserName, setOtherUserName] = useState('Member');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // 1. Get current user ID
    api.get('/auth/status')
      .then(res => setCurrentUserId(res.user.id))
      .catch(console.error);

    // 2. Fetch the other user's full name from their profile
    api.get(`/profiles/${userId}`)
      .then(profile => {
        if (profile && profile.full_name) {
          // You can use profile.full_name.split(' ')[0] for just their first name
          setOtherUserName(profile.full_name); 
        }
      })
      .catch(console.error);

    // 3. Start polling for messages
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [userId]);
/* In case I want to use this later
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
*/
  const fetchMessages = async () => {
    try {
      const response = await api.get(`/messages/${userId}`);
      setMessages(response);
    } catch (error) {
      console.error("Error fetching chat history:", error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const response = await api.post('/messages/', {
        receiver_id: userId,
        content: newMessage
      });
      setMessages([...messages, response]);
      setNewMessage('');
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Helper to ensure the timestamp is treated as UTC so it converts to local time correctly
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const dateStr = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z';
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="chat-container">
      <div className="chat-header panel" style={{ marginBottom: '1rem', padding: '1rem' }}>
        <h2 style={{ margin: 0 }}>Chat with {otherUserName}</h2>
        <a href="/messages" style={{ fontSize: '0.9rem' }}>&larr; Back to Inbox</a>
      </div>
      
      <div className="chat-history panel">
        {messages.map((msg) => {
          const isMe = msg.sender_id === currentUserId;
          return (
            <div 
              key={msg.id} 
              className={`message-bubble ${isMe ? 'sent' : 'received'}`}
              style={{
                textAlign: isMe ? 'right' : 'left',
                margin: '10px 0'
              }}
            >
              <div 
                style={{ 
                  display: 'inline-block', 
                  padding: '10px 15px', 
                  borderRadius: '15px',
                  backgroundColor: isMe ? '#00529b' : '#f0f0f0',
                  color: isMe ? 'white' : 'black',
                  maxWidth: '70%'
                }}
              >
                <p style={{ margin: 0 }}>{msg.content}</p>
              </div>
              
              <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '4px' }}>
                {/* THIS IS WHERE THE NAME AND FIXED TIME SHOW UP */}
                <strong>{isMe ? 'Me' : otherUserName}</strong> &bull; {formatTime(msg.timestamp)}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className="chat-input-form" style={{ marginTop: '1rem', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          style={{ flexGrow: 1 }}
          required
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}