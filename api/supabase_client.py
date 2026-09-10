import os
from supabase import Client, create_client


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()


_client: Client | None = None


def get_client() -> Client | None:
    global _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def is_enabled() -> bool:
    return get_client() is not None


def insert_order(order: dict) -> dict:
    client = get_client()
    if client is None:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    response = client.table("orders").insert(order).execute()
    return response.data[0] if response.data else order


def update_order(order_id: str, updates: dict) -> dict | None:
    client = get_client()
    if client is None:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    response = client.table("orders").update(updates).eq("id", order_id).execute()
    return response.data[0] if response.data else None


def get_order(order_id: str) -> dict | None:
    client = get_client()
    if client is None:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    response = client.table("orders").select("*").eq("id", order_id).limit(1).execute()
    return response.data[0] if response.data else None


def get_order_by_invoice(invoice_number: str) -> dict | None:
    client = get_client()
    if client is None:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    response = client.table("orders").select("*").eq("invoice_number", invoice_number).limit(1).execute()
    return response.data[0] if response.data else None


def list_orders() -> list[dict]:
    client = get_client()
    if client is None:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    response = client.table("orders").select("*").order("created_at", desc=True).execute()
    return response.data or []
