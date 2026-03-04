import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface PricingTier {
  name: string;
  price: string;
  features: string[];
}

export default function Pricing() {
  const navigate = useNavigate();
  const [tiers, setTiers] = useState<Record<string, PricingTier> | null>(null);

  useEffect(() => {
    document.title = 'Pricing — Reepo.dev';
    fetch('/api/pricing')
      .then((r) => r.json())
      .then((data) => setTiers(data.tiers))
      .catch(() => {});
  }, []);

  const defaultTiers: Record<string, PricingTier> = tiers || {
    free: { name: 'Free', price: '$0', features: ['Search and browse all repos', 'View Reepo Scores', 'Up to 3 collections', '100 API requests/day', 'Community features'] },
    pro: { name: 'Pro', price: '$9/mo or $79/yr', features: ['Everything in Free', 'Unlimited collections', 'Comparison tool', 'Export to JSON/CSV', '10,000 API requests/day', 'No ads', 'Priority support'] },
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl sm:text-4xl font-bold text-white">Simple, transparent pricing</h1>
        <p className="mt-3 text-gray-400 text-lg">Start free, upgrade when you need more</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
        {Object.entries(defaultTiers).map(([key, tier]) => (
          <div key={key} className={`card p-6 sm:p-8 ${key === 'pro' ? 'border-accent ring-1 ring-accent/30' : ''}`}>
            {key === 'pro' && (
              <span className="inline-block bg-accent/10 text-accent text-xs font-semibold px-3 py-1 rounded-full mb-4">Most popular</span>
            )}
            <h2 className="text-xl font-bold text-white">{tier.name}</h2>
            <p className="text-2xl font-bold text-white mt-2">{tier.price}</p>
            <ul className="mt-6 space-y-3">
              {tier.features.map((feature, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <svg className="w-4 h-4 text-score-green mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
            <button
              onClick={() => key === 'pro' ? navigate('/search') : undefined}
              className={`mt-8 w-full py-2.5 rounded-lg font-medium text-sm transition-colors ${key === 'pro' ? 'btn-primary' : 'btn-secondary'}`}
            >
              {key === 'pro' ? 'Get Pro' : 'Get started'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
