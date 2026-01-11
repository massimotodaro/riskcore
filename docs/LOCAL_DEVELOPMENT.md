# RISKCORE Local Development

> Last Updated: 2026-01-11
> Status: Active

---

## Prerequisites

- **Docker Desktop** - Running
- **Supabase CLI** - Installed via Scoop (v2.67.1+)
- **Project linked** - `vukinjdeddwwlaumtfij`

---

## Quick Start

```powershell
cd C:\Users\massi\Desktop\RISKCORE
supabase start
```

Open **http://127.0.0.1:54323** for local Studio.

---

## Local Environment URLs

| Service | URL |
|---------|-----|
| **Studio (Dashboard)** | http://127.0.0.1:54323 |
| **API** | http://127.0.0.1:54321 |
| **Database** | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` |
| **GraphQL** | http://127.0.0.1:54321/graphql/v1 |
| **Inbucket (Email)** | http://127.0.0.1:54324 |
| **Edge Functions** | http://127.0.0.1:54321/functions/v1 |

---

## Local Auth Keys

```
Publishable: sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH
Secret:      sb_secret_N7UND0UgjKTVK-Uodkm0Hg_xSvEMPvz
```

---

## Common Commands

| Command | Purpose |
|---------|---------|
| `supabase start` | Start local environment |
| `supabase stop` | Stop local environment |
| `supabase status` | Check what's running |
| `supabase db reset` | Wipe local DB, reapply migrations |
| `supabase db pull` | Download production schema |
| `supabase db push` | Deploy migrations to production |
| `supabase db diff` | Compare local vs production |
| `supabase migration list` | Show migration status |
| `supabase migration new <name>` | Create new migration file |

---

## Workflow: Schema Changes

### 1. Make Changes Locally

Edit schema in local Studio (http://127.0.0.1:54323) or write SQL.

### 2. Generate Migration

```powershell
supabase db diff -f my_change_name
```

Creates `supabase/migrations/[timestamp]_my_change_name.sql`

### 3. Test Locally

```powershell
supabase db reset
```

Reapplies all migrations to verify they work.

### 4. Deploy to Production

```powershell
supabase db push
```

---

## Workflow: Pull Production Changes

If someone else made changes in production:

```powershell
supabase db pull
```

---

## Project Structure

```
C:\Users\massi\Desktop\RISKCORE\
├── supabase/
│   ├── config.toml           # Supabase configuration
│   ├── migrations/           # SQL migration files
│   │   ├── 20260111073517_remote_schema.sql
│   │   └── 20260111074636_remote_schema.sql
│   └── seed.sql              # (optional) Seed data
├── backend/                  # Python FastAPI (future)
├── frontend/                 # React + Tailwind (future)
└── docs/                     # Documentation
```

---

## Troubleshooting

### "Docker not running"
Start Docker Desktop, wait for it to load.

### "Port already in use"
```powershell
supabase stop
supabase start
```

### "Access token not provided"
```powershell
supabase login
```

### "Project not linked"
```powershell
supabase link --project-ref vukinjdeddwwlaumtfij --password YOUR_DB_PASSWORD
```

### Check status
```powershell
supabase status
```

---

## Production vs Local

| Aspect | Production | Local |
|--------|------------|-------|
| URL | `vukinjdeddwwlaumtfij.supabase.co` | `127.0.0.1:54321` |
| Database | Supabase cloud | Docker container |
| Studio | `supabase.com/dashboard` | `127.0.0.1:54323` |
| Data | Real data | Test data only |
| Cost | Usage-based | Free |

---

## Best Practices

1. **Never test schema changes in production** - Use local first
2. **Always pull before making changes** - Stay in sync
3. **Use migrations** - Don't make manual changes in production Studio
4. **Reset frequently** - `supabase db reset` catches migration bugs early
5. **Commit migrations to git** - They're your schema source of truth

---

*Local development guide for RISKCORE*
