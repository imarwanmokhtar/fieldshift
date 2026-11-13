-- Field Shift: one row per analysis run. The Python engine (service role) fills it in.
-- Run this in the Supabase SQL editor after 001_field_profiles.sql.

create table public.analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    status text not null default 'pending' check (status in ('pending','running','done','failed')),
    stage text,                                  -- reading_data | comparing | writing | done | failed
    lang text not null default 'ar' check (lang in ('ar','en')),
    scenario jsonb,                              -- optional {"temp_delta_c": 1.5, "rain_factor": 0.8}
    result jsonb,                                -- the evidence pack
    narrative jsonb,                             -- the farmer-facing text
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index analyses_user_created_idx on public.analyses (user_id, created_at desc);

alter table public.analyses enable row level security;

create policy "own select" on public.analyses
    for select using (auth.uid() = user_id);

-- Users may only create an empty, pending row for themselves.
create policy "own insert" on public.analyses
    for insert with check (
        auth.uid() = user_id and status = 'pending'
        and result is null and narrative is null and error is null
    );

-- Lets the Next.js route remove its own row if the engine could not be reached.
create policy "own delete" on public.analyses
    for delete using (auth.uid() = user_id);

-- No update policy: only the engine (service role) updates rows.

-- set_updated_at() was created in 001_field_profiles.sql
create trigger set_updated_at_analyses
before update on public.analyses
for each row execute procedure public.set_updated_at();
