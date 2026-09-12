create table if not exists public.orders (
    id text primary key,
    invoice_number text unique not null,
    created_at text not null,
    company_name text,
    sector text,
    whatsapp text,
    email text,
    city_country text,
    options_json jsonb not null default '[]'::jsonb,
    items_json jsonb not null default '[]'::jsonb,
    total_fcfa integer not null,
    status text not null,
    payment_status text not null default 'EN_ATTENTE_DE_PAIEMENT',
    project_status text not null default 'NON_DEMARRE',
    payment_method text,
    payment_phone text,
    transaction_id text,
    paid_at text
);

alter table public.orders add column if not exists payment_status text;
alter table public.orders add column if not exists project_status text;
update public.orders
set payment_status = case when status in ('PAYE', 'EN_COURS', 'LIVRE') then 'PAYE' else 'EN_ATTENTE_DE_PAIEMENT' end
where payment_status is null;
update public.orders
set project_status = case when status = 'EN_COURS' then 'EN_COURS' when status = 'LIVRE' then 'LIVRE' else 'NON_DEMARRE' end
where project_status is null;
alter table public.orders alter column payment_status set default 'EN_ATTENTE_DE_PAIEMENT';
alter table public.orders alter column project_status set default 'NON_DEMARRE';

alter table public.orders enable row level security;

revoke all on table public.orders from anon, authenticated;
grant all on table public.orders to service_role;