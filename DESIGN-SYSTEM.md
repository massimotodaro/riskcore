# RISKCORE Design System - MANDATORY REFERENCE

## BEFORE ANY CSS/STYLING CHANGES
Read this entire file. Match ALL values exactly.

## Colors (Use ONLY these)
```css
/* Backgrounds */
bg-primary: #0f172a (use: bg-[#0f172a])
bg-card: #1e293b (use: bg-[#1e293b])

/* Brand */
blue-primary: #3b82f6 (use: text-blue-500 or bg-blue-500)
green-success: #22c55e (use: text-green-500)
purple-premium: #a855f7 (use: text-purple-500)

/* Text */
text-primary: #f1f5f9 (use: text-slate-100)
text-secondary: #94a3b8 (use: text-slate-400)
text-muted: #64748b (use: text-slate-500)
```

## Spacing (Use ONLY these values)
- Section padding: py-24 (96px vertical)
- Card padding: p-6 (24px)
- Gap between cards: gap-6 (24px)
- Container max-width: max-w-7xl mx-auto px-6

## Typography
- H1: text-5xl md:text-6xl font-bold font-['Space_Grotesk']
- H2: text-3xl md:text-4xl font-bold font-['Space_Grotesk']
- H3: text-xl font-semibold
- Body: text-base text-slate-300
- Small: text-sm text-slate-400

## Card Component (EXACT pattern)
```jsx
<div className="bg-[#1e293b]/90 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:border-blue-500/30 hover:-translate-y-1 transition-all duration-300">
  {/* content */}
</div>
```

## Button Patterns
```jsx
// Primary
<button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors">

// Secondary  
<button className="border border-white/20 hover:border-white/40 text-white font-semibold px-6 py-3 rounded-lg transition-colors">
```

## COMMON MISTAKES TO AVOID
- ❌ Don't use bg-slate-800 (use bg-[#1e293b] instead)
- ❌ Don't use rounded-lg on cards (use rounded-2xl)
- ❌ Don't use py-16 for sections (use py-24)
- ❌ Don't add shadows without blur (always add backdrop-blur)