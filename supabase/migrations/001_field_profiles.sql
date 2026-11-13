-- Field Shift farmer onboarding profile table
-- One profile per user for now (one field). Multi-field support will change
-- user_id to non-unique and add a field_id later.

create table public.field_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,
    answers jsonb not null default '{}'::jsonb,
    current_step int not null default 0,
    status text not null default 'in_progress' check (status in ('in_progress','completed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.field_profiles enable row level security;

create policy "own select" on public.field_profiles
    for select using (auth.uid() = user_id);

create policy "own insert" on public.field_profiles
    for insert with check (auth.uid() = user_id);

create policy "own update" on public.field_profiles
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own delete" on public.field_profiles
    for delete using (auth.uid() = user_id);

-- keep updated_at fresh with a trigger
create extension if not exists "pgcrypto";
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger set_updated_at_field_profiles
before update on public.field_profiles
for each row execute procedure public.set_updated_at();