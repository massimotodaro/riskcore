# Frontend Skill

> React + Tailwind conventions for RISKCORE dashboard

---

## Project Structure

```
/frontend
├── package.json
├── next.config.js
├── tailwind.config.js
├── .env.local.example
├── /src
│   ├── /app                    # Next.js 14 App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Dashboard home
│   │   ├── /portfolios
│   │   │   └── page.tsx
│   │   ├── /risk
│   │   │   └── page.tsx
│   │   └── /settings
│   │       └── page.tsx
│   ├── /components
│   │   ├── /ui                 # Base components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Table.tsx
│   │   │   └── Input.tsx
│   │   ├── /dashboard
│   │   │   ├── FirmOverview.tsx
│   │   │   ├── PortfolioCard.tsx
│   │   │   └── RiskSummary.tsx
│   │   ├── /charts
│   │   │   ├── ExposureChart.tsx
│   │   │   ├── CorrelationMatrix.tsx
│   │   │   └── VaRChart.tsx
│   │   └── /layout
│   │       ├── Navbar.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── /hooks
│   │   ├── usePositions.ts
│   │   ├── useRisk.ts
│   │   └── useSupabase.ts
│   ├── /lib
│   │   ├── supabase.ts
│   │   ├── api.ts
│   │   └── utils.ts
│   └── /types
│       ├── position.ts
│       ├── portfolio.ts
│       └── risk.ts
└── /public
    └── /images
```

---

## Component Pattern

```tsx
// components/dashboard/PortfolioCard.tsx
import { Card } from '@/components/ui/Card';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { Portfolio } from '@/types/portfolio';

interface PortfolioCardProps {
  portfolio: Portfolio;
  onClick?: () => void;
}

export function PortfolioCard({ portfolio, onClick }: PortfolioCardProps) {
  return (
    <Card 
      className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {portfolio.name}
          </h3>
          <p className="text-sm text-gray-500">{portfolio.pm_name}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          portfolio.pnl_today >= 0 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {formatPercent(portfolio.pnl_today)}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">NAV</p>
          <p className="text-lg font-medium">
            {formatCurrency(portfolio.nav)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-500">VaR (95%)</p>
          <p className="text-lg font-medium">
            {formatCurrency(portfolio.var_95)}
          </p>
        </div>
      </div>
    </Card>
  );
}
```

---

## Hook Pattern

```tsx
// hooks/usePositions.ts
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Position } from '@/types/position';

interface UsePositionsOptions {
  portfolioId?: string;
  asOfDate?: string;
}

export function usePositions(options: UsePositionsOptions = {}) {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchPositions() {
      try {
        setLoading(true);
        
        let query = supabase
          .from('positions')
          .select('*, securities(ticker, name, asset_class)');
        
        if (options.portfolioId) {
          query = query.eq('portfolio_id', options.portfolioId);
        }
        if (options.asOfDate) {
          query = query.eq('as_of_date', options.asOfDate);
        }
        
        const { data, error } = await query;
        
        if (error) throw error;
        setPositions(data || []);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchPositions();
  }, [options.portfolioId, options.asOfDate]);

  return { positions, loading, error };
}
```

---

## Real-time Subscription

```tsx
// hooks/useRealtimePositions.ts
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

export function useRealtimePositions(portfolioId: string) {
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    // Initial fetch
    fetchPositions();

    // Subscribe to changes
    const subscription = supabase
      .channel('positions')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'positions',
          filter: `portfolio_id=eq.${portfolioId}`
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setPositions(prev => [...prev, payload.new]);
          } else if (payload.eventType === 'UPDATE') {
            setPositions(prev => 
              prev.map(p => p.id === payload.new.id ? payload.new : p)
            );
          } else if (payload.eventType === 'DELETE') {
            setPositions(prev => 
              prev.filter(p => p.id !== payload.old.id)
            );
          }
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [portfolioId]);

  return positions;
}
```

---

## Supabase Client

```tsx
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

---

## API Client

```tsx
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Positions
  getPositions: (params?: Record<string, string>) => 
    fetchAPI<Position[]>(`/api/v1/positions?${new URLSearchParams(params)}`),
  
  createPosition: (data: PositionCreate) =>
    fetchAPI<Position>('/api/v1/positions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Risk
  getRiskMetrics: (portfolioId?: string) =>
    fetchAPI<RiskMetrics>(`/api/v1/risk/metrics${portfolioId ? `?portfolio_id=${portfolioId}` : ''}`),
  
  getExposures: () =>
    fetchAPI<Exposures>('/api/v1/risk/exposures'),

  // AI
  askQuestion: (question: string) =>
    fetchAPI<AIResponse>('/api/v1/ai/query', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),
};
```

---

## Tailwind Patterns

### Color Palette (Finance-appropriate)

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Primary - Professional blue
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // Success - Green for positive
        success: {
          100: '#dcfce7',
          500: '#22c55e',
          800: '#166534',
        },
        // Danger - Red for negative
        danger: {
          100: '#fee2e2',
          500: '#ef4444',
          800: '#991b1b',
        },
        // Warning - Yellow for alerts
        warning: {
          100: '#fef3c7',
          500: '#f59e0b',
          800: '#92400e',
        },
      },
    },
  },
};
```

### Common Classes

```tsx
// Cards
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">

// Tables
<table className="min-w-full divide-y divide-gray-200">
<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
<td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900">

// Positive/Negative values
<span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>

// Buttons
<button className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">

// Inputs
<input className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent">
```

---

## Chart Components (Recharts)

```tsx
// components/charts/ExposureChart.tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface ExposureChartProps {
  data: Array<{ name: string; value: number }>;
}

export function ExposureChart({ data }: ExposureChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical">
        <XAxis type="number" tickFormatter={(v) => `${v}%`} />
        <YAxis type="category" dataKey="name" width={100} />
        <Tooltip 
          formatter={(value: number) => [`${value.toFixed(2)}%`, 'Exposure']}
        />
        <Bar 
          dataKey="value" 
          fill="#3b82f6"
          radius={[0, 4, 4, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

---

## Utility Functions

```tsx
// lib/utils.ts
export function formatCurrency(
  value: number, 
  currency: string = 'USD'
): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(2)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function cn(...classes: (string | undefined | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
```

---

## Types

```tsx
// types/portfolio.ts
export interface Portfolio {
  id: string;
  name: string;
  pm_name: string;
  fund_id: string;
  strategy: string;
  nav: number;
  pnl_today: number;
  var_95: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// types/position.ts
export interface Position {
  id: string;
  portfolio_id: string;
  security_id: string;
  quantity: number;
  market_value: number;
  cost_basis: number;
  currency: string;
  as_of_date: string;
  securities?: Security;
}

// types/risk.ts
export interface RiskMetrics {
  var_95: number;
  var_99: number;
  cvar_95: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
}
```

---

## Don't

- ❌ Don't use inline styles (use Tailwind)
- ❌ Don't fetch in components (use hooks)
- ❌ Don't hardcode API URLs
- ❌ Don't skip loading states
- ❌ Don't skip error handling
- ❌ Don't use `any` type
- ❌ Don't skip TypeScript

---

*Frontend patterns for RISKCORE*
