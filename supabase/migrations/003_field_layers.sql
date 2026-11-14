-- Field Shift: satellite layers per field, fetched by the Python engine through NASA AppEEARS.
-- One row per user (one field for now). Only the engine (service role) writes it.
-- Run this in the Supabase SQL editor after 002_analyses.sql.

create table public.field_layers (
    user_id uuid primary key references auth.users(id) on delete cascade,
    lat double precision not null,
    lng double precision not null,
    status text not null default 'submitted'
        check (status in ('submitted','processing','partial','done','failed')),
    tasks jsonb not null default '{}'::jsonb,      -- AppEEARS task ids and their status per group
    features jsonb not null default '{}'::jsonb,   -- small processed summaries (NDVI series, ET, SMAP, elevation)
    sources jsonb not null default '[]'::jsonb,    -- provenance: dataset, product ids, resolution, retrieval date
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.field_layers enable row level security;

-- Farmers may read their own layers; no insert/update/delete policies: the engine writes with the service role.
create policy "own select" on public.field_layers
    for select using (auth.uid() = user_id);

-- set_updated_at() was created in 001_field_profiles.sql
create trigger set_updated_at_field_layers
before update on public.field_layers
for each row execute procedure public.set_updated_at();
