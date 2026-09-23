import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { sendMessage } from '../services/chatbot';
import type { ChatMessage } from '../types';
import { SUGGESTED_QUESTIONS } from '../data/chatbot';
import { formatRelativeDate } from '../utils/date';

const SOURCE_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  university: { label: 'University info', color: '#1E3A8A', icon: '🎓' },
  community: { label: 'Community answer', color: '#059669', icon: '💬' },
  general: { label: 'General guidance', color: '#64748B', icon: '💡' },
};

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 mb-4">
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0" style={{ backgroundColor: '#1E3A8A' }}>
        N
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex items-center gap-1">
          {[0, 0.15, 0.3].map((delay, i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-slate-400 animate-bounce"
              style={{ animationDelay: `${delay}s`, animationDuration: '0.8s' }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const source = message.sourceType ? SOURCE_LABELS[message.sourceType] : null;

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-blue-700 text-white rounded-2xl rounded-br-sm px-4 py-3" style={{ backgroundColor: '#1E3A8A' }}>
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-end gap-3 mb-4">
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0 self-start mt-1" style={{ backgroundColor: '#1E3A8A' }}>
        N
      </div>
      <div className="max-w-[80%] space-y-1.5">
        <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3">
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{message.content}</p>
        </div>
        {source && (
          <div className="flex items-center gap-2">
            <span
              className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full border"
              style={{ backgroundColor: `${source.color}10`, color: source.color, borderColor: `${source.color}30` }}
            >
              <span>{source.icon}</span> {source.label}
            </span>
            {message.sourceRef?.questionTitle && (
              <Link
                to={`/forum/${message.sourceRef.questionId}`}
                className="text-xs text-blue-600 hover:underline"
              >
                View source →
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chatbot() {
  const { currentUser, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [cleared, setCleared] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const firstName = currentUser?.fullName.split(' ')[0];

  const welcomeMessage: ChatMessage = {
    id: 'welcome',
    role: 'assistant',
    content: isAuthenticated && firstName
      ? `Hi ${firstName}! 👋 I'm Navi, your Newcomer Navigation assistant. I'm here to help you settle in at Bennett University, Greater Noida.\n\nYou can ask me about hostel life, finding your department, campus facilities, courses, and much more. What would you like to know?`
      : `Hello! 👋 I'm Navi, your Newcomer Navigation assistant for Bennett University, Greater Noida.\n\nI can help you find answers about campus life, courses, facilities, and more. Sign in to get a more personalised experience!\n\nWhat would you like to know?`,
    timestamp: new Date().toISOString(),
    sourceType: 'general',
  };

  async function handleSend(text?: string) {
    const content = (text || input).trim();
    if (!content || loading) return;
    setInput('');

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-u`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });

    try {
      const response = await sendMessage(content);
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}-a`,
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString(),
        sourceType: response.sourceType,
        sourceRef: response.sourceRef,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: `msg-${Date.now()}-e`,
        role: 'assistant',
        content: "I'm having trouble responding right now. Please try again in a moment, or check the community forum for help.",
        timestamp: new Date().toISOString(),
        sourceType: 'general',
      };
      setMessages(prev => [...prev, errorMsg]);
    }
    setLoading(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleClear() {
    if (messages.length === 0) return;
    setMessages([]);
    setCleared(true);
    setTimeout(() => setCleared(false), 2000);
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="flex flex-col h-[calc(100vh-3.75rem)]" style={{ maxHeight: 'calc(100vh - 3.75rem)' }}>
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 sm:px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-sm" style={{ backgroundColor: '#1E3A8A' }}>
            N
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800" style={{ fontFamily: 'var(--font-display)' }}>
              Navi — Newcomer Assistant
            </h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <p className="text-xs text-slate-500">
                Demo mode — AI-powered responses coming soon
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={handleClear}
              className="px-3 py-2 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            >
              {cleared ? '✓ Cleared' : 'Clear chat'}
            </button>
          )}
          {!isAuthenticated && (
            <Link
              to="/?mode=signin"
              className="px-3 py-2 text-xs font-medium text-white rounded-lg"
              style={{ backgroundColor: '#1E3A8A' }}
            >
              Sign in
            </Link>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4" style={{ background: '#F8FAFC' }}>
        <div className="max-w-3xl mx-auto">
          {/* Welcome message */}
          <MessageBubble message={welcomeMessage} />

          {/* Suggested questions — show only when no messages */}
          {messages.length === 0 && (
            <div className="mb-6">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3 ml-11">Try asking</p>
              <div className="flex flex-wrap gap-2 ml-11">
                {SUGGESTED_QUESTIONS.map(q => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-4 py-2 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 bg-white border-t border-slate-200 px-4 sm:px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about Bennett University…"
                rows={1}
                className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors resize-none leading-relaxed"
                style={{ maxHeight: '120px', overflowY: 'auto' }}
              />
            </div>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#1E3A8A' }}
              aria-label="Send message"
            >
              {loading ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="animate-spin" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.2"/>
                  <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              )}
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">
            Press <kbd className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-500 font-mono text-[10px]">Enter</kbd> to send · Shift+Enter for new line · Navi uses a demo knowledge base — verify important details with official Bennett University sources.
          </p>
        </div>
      </div>
    </div>
  );
}
