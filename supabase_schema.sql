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
    payment_method text,
    payment_phone text,
    transaction_id text,
    paid_at text
);

alter table public.orders enable row level security;

revoke all on table public.orders from anon, authenticated;
grant all on table public.orders to service_role;