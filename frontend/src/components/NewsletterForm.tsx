import { useState } from 'react';

export default function NewsletterForm() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('loading');
    fetch('/api/newsletter/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
      .then((r) => {
        if (!r.ok) throw new Error();
        setStatus('success');
        setEmail('');
      })
      .catch(() => setStatus('error'));
  };

  if (status === 'success') {
    return <p className="text-sm text-score-green">Subscribed! Check your inbox.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Weekly AI digest"
        className="bg-bg-card border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:border-accent focus:outline-none w-48"
      />
      <button type="submit" disabled={status === 'loading'} className="btn-primary text-xs py-1.5 px-3">
        {status === 'loading' ? '...' : 'Subscribe'}
      </button>
      {status === 'error' && <span className="text-xs text-score-red">Failed</span>}
    </form>
  );
}
