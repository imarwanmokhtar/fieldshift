-- Field Shift: several fields per user.
-- Run this in the Supabase SQL editor after 003_field_layers.sql.
--
-- 1. field_profiles: one row per FIELD (was one per user).
-- 2. analyses: each analysis belongs to a field (existing rows are linked to the user's field).
-- 3. field_layers: satellite data per field. The table only caches NASA results that the
--    engine can fetch again, so it is recreated (the next analysis requests SMAP again).

-- 1. Allow several profiles (fields) per user.
alter table public.field_profiles drop constraint if exists field_profiles_user_id_key;
create index if not exists field_profiles_user_updated_idx
    on public.field_profiles (user_id, updated_at desc);

-- 2. Link analyses to a field.
alter table public.analyses
    add column if not exists field_id uuid references public.field_profiles(id) on delete cascade;

-- Until now each user had exactly one field: attach their existing analyses to it.
update public.analyses a
set field_id = fp.id
from public.field_profiles fp
where a.field_id is null and fp.user_id = a.user_id;

create index if not exists analyses_field_created_idx
    on public.analyses (field_id, created_at desc);

-- Users may only start analyses on their own fields.
drop policy if exists "own insert" on public.analyses;
create policy "own insert" on public.analyses
    for insert with check (
        auth.uid() = user_id and status = 'pending'
        and result is null and narrative is null and error is null
        and (field_id is null or exists (
            select 1 from public.field_profiles fp
            where fp.id = field_id and fp.user_id = auth.uid()
        ))
    );

-- 3. Satellite layers per field.
drop table if exists public.field_layers;

create table public.field_layers (
    field_id uuid primary key references public.field_profiles(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    lat double precision not null,
    lng double precision not null,
    status text not null default 'submitted'
        check (status in ('submitted','processing','partial','done','failed')),
    tasks jsonb not null default '{}'::jsonb,      -- AppEEARS task ids and their status
    features jsonb not null default '{}'::jsonb,   -- small processed summaries (SMAP)
    sources jsonb not null default '[]'::jsonb,    -- provenance: dataset, product ids, resolution, retrieval date
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.field_layers enable row level security;

-- Farmers may read their own layers; only the engine (service role) writes.
create policy "own select" on public.field_layers
    for select using (auth.uid() = user_id);

create trigger set_updated_at_field_layers
before update on public.field_layers
for each row execute procedure public.set_updated_at();
