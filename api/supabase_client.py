import json
import os
import urllib.error
import urllib.parse
import urllib.request


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().strip('"').strip("'").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip().strip('"').strip("'")

for suffix in ("/rest/v1/orders", "/rest/v1", "/"):
    if SUPABASE_URL.endswith(suffix):
        SUPABASE_URL = SUPABASE_URL[:-len(suffix)].rstrip("/")
        break

TABLE_URL = f"{SUPABASE_URL}/rest/v1/orders" if SUPABASE_URL and SUPABASE_KEY else ""
NOTIFICATIONS_URL = f"{SUPABASE_URL}/rest/v1/notifications" if SUPABASE_URL and SUPABASE_KEY else ""


def is_enabled():
    return bool(TABLE_URL)


def request(method, query="", payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_data = urllib.request.Request(TABLE_URL + query, data=body, method=method)
    request_data.add_header("apikey", SUPABASE_KEY)
    request_data.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    request_data.add_header("Content-Type", "application/json")
    request_data.add_header("Prefer", "return=representation")

    try:
        with urllib.request.urlopen(request_data, timeout=15) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else []
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase HTTP {error.code}: {details}") from error


def insert_order(order):
    rows = request("POST", payload=order)
    return rows[0] if rows else order


def update_order(order_id, updates):
    query = f"?id=eq.{urllib.parse.quote(order_id, safe='')}"
    rows = request("PATCH", query=query, payload=updates)
    return rows[0] if rows else None


def get_order(order_id):
    query = f"?id=eq.{urllib.parse.quote(order_id, safe='')}&limit=1"
    rows = request("GET", query=query)
    return rows[0] if rows else None


def get_order_by_invoice(invoice_number):
    query = f"?invoice_number=eq.{urllib.parse.quote(invoice_number, safe='')}&limit=1"
    rows = request("GET", query=query)
    return rows[0] if rows else None


def list_orders():
    return request("GET", query="?select=*&order=created_at.desc")


def notification_request(method, query="", payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_data = urllib.request.Request(NOTIFICATIONS_URL + query, data=body, method=method)
    request_data.add_header("apikey", SUPABASE_KEY)
    request_data.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    request_data.add_header("Content-Type", "application/json")
    request_data.add_header("Prefer", "return=representation")
    try:
        with urllib.request.urlopen(request_data, timeout=15) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else []
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase notifications HTTP {error.code}: {details}") from error


def insert_notification(notification):
    rows = notification_request("POST", payload=notification)
    return rows[0] if rows else notification


def list_notifications():
    return notification_request("GET", query="?select=*&order=created_at.desc")
