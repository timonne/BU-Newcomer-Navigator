import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { CATEGORIES, TAGS } from '../../data/categories';
import { submitQuestion } from '../../services/forum';
import LoadingSpinner from '../common/LoadingSpinner';

interface AskQuestionModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function AskQuestionModal({ onClose, onSuccess }: AskQuestionModalProps) {
  const { currentUser } = useAuth();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function toggleTag(id: string) {
    setSelectedTags(prev => prev.includes(id) ? prev.filter(t => t !== id) : prev.length < 4 ? [...prev, id] : prev);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!title.trim() || title.trim().length < 10) newErrors.title = 'Title must be at least 10 characters.';
    if (!body.trim() || body.trim().length < 20) newErrors.body = 'Description must be at least 20 characters.';
    if (!categoryId) newErrors.category = 'Please select a category.';
    if (Object.keys(newErrors).length > 0) return setErrors(newErrors);

    setLoading(true);
    await submitQuestion({
      title: title.trim(),
      body: body.trim(),
      authorId: currentUser!.id,
      categoryId,
      tags: selectedTags,
    });
    setLoading(false);
    onSuccess();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-semibold text-slate-800" style={{ fontFamily: 'var(--font-display)' }}>Ask a Question</h2>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-400 hover:bg-slate-100 transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Question title <span className="text-red-500">*</span></label>
            <input
              value={title}
              onChange={e => { setTitle(e.target.value); setErrors(p => ({ ...p, title: '' })); }}
              placeholder="e.g. How does the hostel room allocation work for freshers?"
              className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors ${errors.title ? 'border-red-400 bg-red-50' : 'border-slate-300'}`}
            />
            {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title}</p>}
          </div>

          {/* Body */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Detailed description <span className="text-red-500">*</span></label>
            <textarea
              value={body}
              onChange={e => { setBody(e.target.value); setErrors(p => ({ ...p, body: '' })); }}
              placeholder="Provide context, what you've tried, and what specific help you need…"
              rows={5}
              className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors resize-none ${errors.body ? 'border-red-400 bg-red-50' : 'border-slate-300'}`}
            />
            {errors.body && <p className="text-xs text-red-600 mt-1">{errors.body}</p>}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Category <span className="text-red-500">*</span></label>
            <select
              value={categoryId}
              onChange={e => { setCategoryId(e.target.value); setErrors(p => ({ ...p, category: '' })); }}
              className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors bg-white ${errors.category ? 'border-red-400' : 'border-slate-300'}`}
            >
              <option value="">Select a category…</option>
              <optgroup label="Academic">
                {CATEGORIES.filter(c => c.type === 'academic').map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </optgroup>
              <optgroup label="Non-academic">
                {CATEGORIES.filter(c => c.type === 'non-academic').map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </optgroup>
            </select>
            {errors.category && <p className="text-xs text-red-600 mt-1">{errors.category}</p>}
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Tags <span className="text-slate-400 font-normal">(up to 4)</span></label>
            <div className="flex flex-wrap gap-2">
              {TAGS.map(tag => (
                <button
                  type="button"
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                    selectedTags.includes(tag.id)
                      ? 'text-white border-transparent'
                      : 'bg-white text-slate-600 border-slate-300 hover:border-slate-400'
                  }`}
                  style={selectedTags.includes(tag.id) ? { backgroundColor: tag.color, borderColor: tag.color } : {}}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
            <button type="button" onClick={onClose} className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-60"
              style={{ backgroundColor: '#1E3A8A' }}
            >
              {loading && <LoadingSpinner size={14} />}
              Post Question
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
