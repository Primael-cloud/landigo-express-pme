import http.server
import socketserver
import json
import os
import sqlite3
import urllib.parse
import urllib.error
import urllib.request
import uuid
import smtplib
from email.message import EmailMessage
from datetime import datetime

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BRIEFS_DIR = os.path.join(DATA_DIR, "briefs")
INVOICES_DIR = os.path.join(DATA_DIR, "invoices")
DB_PATH = os.path.join(DATA_DIR, "landigo.db")

os.makedirs(BRIEFS_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)

# Helper to load .env variables if present
def load_env():
    env_file = os.path.join(BASE_DIR, ".env")
    env_vars = {
        "DOMAIN_NAME": "https://landigo-express.com",
        "CINETPAY_MODE": "sandbox",
        "CINETPAY_SITE_ID": "1053457",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "landigo2026!",
        "TOKEN": "landigo_admin_token_2026",
        "SUPABASE_URL": "",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "SMTP_HOST": "",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "NOTIFICATION_FROM": ""
    }
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    for key in env_vars:
        if os.environ.get(key):
            env_vars[key] = os.environ[key]
    return env_vars

ENV = load_env()


class SupabaseStore:
    """Small REST client for Supabase with SQLite fallback for local use."""

    def __init__(self):
        self.url = ENV.get("SUPABASE_URL", "").rstrip("/")
        self.key = ENV.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.table_url = f"{self.url}/rest/v1/orders" if self.url and self.key else ""

    @property
    def enabled(self):
        return bool(self.table_url)

    def request(self, method, query="", payload=None):
        url = self.table_url + query
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("apikey", self.key)
        request.add_header("Authorization", f"Bearer {self.key}")
        request.add_header("Content-Type", "application/json")
        request.add_header("Prefer", "return=representation")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode("utf-8")
                return json.loads(content) if content else []
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {error.code}: {details}") from error

    def insert(self, record):
        return self.request("POST", payload=record)

    def update(self, query, updates):
        return self.request("PATCH", query=query, payload=updates)

    def select(self, query=""):
        return self.request("GET", query=query)


STORE = SupabaseStore()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            invoice_number TEXT UNIQUE,
            created_at TEXT,
            company_name TEXT,
            sector TEXT,
            whatsapp TEXT,
            email TEXT,
            city_country TEXT,
            options_json TEXT,
            items_json TEXT,
            total_fcfa INTEGER,
            status TEXT,
            payment_status TEXT,
            project_status TEXT,
            payment_method TEXT,
            payment_phone TEXT,
            transaction_id TEXT,
            paid_at TEXT
        )
    ''')
    conn.commit()
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(orders)").fetchall()}
    if "payment_status" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT")
    if "project_status" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN project_status TEXT")
    cursor.execute("UPDATE orders SET payment_status = CASE WHEN status IN ('PAYE', 'EN_COURS', 'LIVRE') THEN 'PAYE' ELSE 'EN_ATTENTE_DE_PAIEMENT' END WHERE payment_status IS NULL")
    cursor.execute("UPDATE orders SET project_status = CASE WHEN status = 'EN_COURS' THEN 'EN_COURS' WHEN status = 'LIVRE' THEN 'LIVRE' ELSE 'NON_DEMARRE' END WHERE project_status IS NULL")
    conn.close()

init_db()


def as_json_value(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value or []


def order_for_supabase(data):
    return {
        "id": data["id"],
        "invoice_number": data["invoice_number"],
        "created_at": data["created_at"],
        "company_name": data.get("company_name"),
        "sector": data.get("sector"),
        "whatsapp": data.get("whatsapp"),
        "email": data.get("email"),
        "city_country": data.get("city_country"),
        "options_json": data.get("options", data.get("options_json", [])),
        "items_json": data.get("items", data.get("items_json", [])),
        "total_fcfa": data["total_fcfa"],
        "status": data["status"],
        "payment_status": data.get("payment_status", data.get("status", "EN_ATTENTE_DE_PAIEMENT")),
        "project_status": data.get("project_status", "NON_DEMARRE"),
        "payment_method": data.get("payment_method"),
        "payment_phone": data.get("payment_phone"),
        "transaction_id": data.get("transaction_id"),
        "paid_at": data.get("paid_at"),
    }


def insert_order(order):
    if STORE.enabled:
        STORE.insert(order_for_supabase(order))
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (id, invoice_number, created_at, company_name, sector, whatsapp, email, city_country, options_json, items_json, total_fcfa, status, payment_status, project_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order["id"], order["invoice_number"], order["created_at"], order["company_name"],
        order["sector"], order["whatsapp"], order["email"], order["city_country"],
        json.dumps(order["options"]), json.dumps(order["items"]), order["total_fcfa"], order["status"],
        order.get("payment_status", order["status"]), order.get("project_status", "NON_DEMARRE")
    ))
    conn.commit()
    conn.close()


def update_order(order_id, updates):
    if STORE.enabled:
        rows = STORE.update(f"?id=eq.{urllib.parse.quote(order_id, safe='')}", updates)
        return rows[0] if rows else None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    assignments = ", ".join(f"{key} = ?" for key in updates)
    cursor.execute(f"UPDATE orders SET {assignments} WHERE id = ?", (*updates.values(), order_id))
    conn.commit()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_order(order_id):
    if STORE.enabled:
        rows = STORE.select(f"?id=eq.{urllib.parse.quote(order_id, safe='')}&limit=1")
        return rows[0] if rows else None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def list_orders():
    if STORE.enabled:
        return STORE.select("?select=*&order=created_at.desc")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def order_response(row):
    if isinstance(row, sqlite3.Row):
        get = row.__getitem__
        return {
            "id": get("id"), "invoice_number": get("invoice_number"), "created_at": get("created_at"),
            "company_name": get("company_name"), "sector": get("sector"), "whatsapp": get("whatsapp"), "email": get("email"),
            "city_country": get("city_country"), "options": as_json_value(get("options_json")),
            "items": as_json_value(get("items_json")),
            "total_fcfa": get("total_fcfa"), "status": get("status"),
            "payment_status": get("payment_status") or get("status"), "project_status": get("project_status") or "NON_DEMARRE",
            "payment_method": get("payment_method"), "payment_phone": get("payment_phone"),
            "transaction_id": get("transaction_id"), "paid_at": get("paid_at")
        }

    return {
        "id": row.get("id"), "invoice_number": row.get("invoice_number"), "created_at": row.get("created_at"),
        "company_name": row.get("company_name"), "sector": row.get("sector"), "whatsapp": row.get("whatsapp"), "email": row.get("email"),
        "city_country": row.get("city_country"), "options": as_json_value(row.get("options", row.get("options_json"))),
        "items": as_json_value(row.get("items", row.get("items_json"))),
        "total_fcfa": row.get("total_fcfa"), "status": row.get("status"),
        "payment_status": row.get("payment_status") or row.get("status"), "project_status": row.get("project_status") or "NON_DEMARRE",
        "payment_method": row.get("payment_method"), "payment_phone": row.get("payment_phone"),
        "transaction_id": row.get("transaction_id"), "paid_at": row.get("paid_at")
    }


def parse_datetime(value):
    try:
        return datetime.strptime(value, "%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return None


def send_client_notification(order, message):
    host = ENV.get("SMTP_HOST", "")
    username = ENV.get("SMTP_USERNAME", "")
    password = ENV.get("SMTP_PASSWORD", "")
    recipient = order.get("email")
    if not host or not username or not password or not recipient or recipient == "N/A":
        return {"email_sent": False, "reason": "SMTP non configuré ou email client absent"}

    email = EmailMessage()
    email["Subject"] = f"Mise à jour de votre projet Landigo - {order['invoice_number']}"
    email["From"] = ENV.get("NOTIFICATION_FROM") or username
    email["To"] = recipient
    email.set_content(f"Bonjour {order.get('company_name', '')},\n\n{message}\n\nRéférence : {order['invoice_number']}\n\nL'équipe Landigo Express")
    try:
        with smtplib.SMTP(host, int(ENV.get("SMTP_PORT", "587")), timeout=15) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(email)
        return {"email_sent": True}
    except (OSError, smtplib.SMTPException, ValueError) as error:
        print(f"Erreur notification email: {error}")
        return {"email_sent": False, "reason": "Échec de l'envoi email"}


def project_status_message(status):
    return {
        "EN_COURS": "Votre paiement a été confirmé et votre projet est maintenant en cours de réalisation.",
        "LIVRE": "Votre projet est terminé et disponible pour livraison. Merci pour votre confiance.",
        "PROBLEME": "Nous rencontrons un problème dans la réalisation de votre projet. Notre équipe vous contactera rapidement.",
    }.get(status, f"Le statut de votre projet est maintenant : {status}.")


def refresh_project_statuses():
    now = datetime.now()
    for row in list_orders():
        order = order_response(row)
        paid_at = parse_datetime(order.get("paid_at"))
        if (order.get("payment_status") == "PAYE" and order.get("project_status") == "NON_DEMARRE"
                and paid_at and (now - paid_at).total_seconds() >= 24 * 60 * 60):
            updated = update_order(order["id"], {"project_status": "EN_COURS", "status": "EN_COURS"})
            if updated:
                send_client_notification(order_response(updated), project_status_message("EN_COURS"))

class LandigoHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed_path = urllib.parse.urlparse(path).path
        if parsed_path == '/':
            return os.path.join(BASE_DIR, 'index.html')
        elif parsed_path == '/admin-login':
            return os.path.join(BASE_DIR, 'admin_login.html')
        elif parsed_path == '/admin':
            return os.path.join(BASE_DIR, 'admin.html')
        return super().translate_path(path)

    def is_authenticated(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        return token == ENV.get("TOKEN", "landigo_admin_token_2026")

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/admin/orders':
            if not self.is_authenticated():
                self.send_json({"error": "Non autorise"}, status=401)
                return
            self.handle_get_orders()
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if self.path == '/api/admin/login':
            self.handle_admin_login(data)
        elif self.path == '/api/brief':
            self.handle_create_brief(data)
        elif self.path == '/api/chat':
            self.handle_chat(data)
        elif self.path == '/api/payment/simulate':
            self.handle_payment_simulation(data)
        elif self.path == '/api/cinetpay/notify':
            self.handle_cinetpay_webhook(data)
        elif self.path == '/api/admin/update_status':
            if not self.is_authenticated():
                self.send_json({"error": "Non autorise"}, status=401)
                return
            self.handle_update_status(data)
        else:
            self.send_json({'error': 'Endpoint non trouve'}, status=404)

    def send_json(self, response_data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def handle_admin_login(self, data):
        u = data.get("username", "")
        p = data.get("password", "")
        if u == ENV.get("ADMIN_USERNAME", "admin") and p == ENV.get("ADMIN_PASSWORD", "landigo2026!"):
            self.send_json({
                "success": True,
                "token": ENV.get("TOKEN", "landigo_admin_token_2026"),
                "message": "Authentification reussie"
            })
        else:
            self.send_json({"success": False, "error": "Identifiants invalides"}, status=401)

    def handle_create_brief(self, data):
        ref_id = str(uuid.uuid4())[:8].upper()
        invoice_num = f"FAC-LANDIGO-{datetime.now().year}-{ref_id}"

        base_price = 45000
        options = data.get('options', [])
        
        items = [
            {"description": "Conception & Design Landing Page Sur-Mesure TPE/PME (Responsive & SEO)", "amount": base_price}
        ]

        total = base_price

        if "whatsapp_direct" in options:
            items.append({"description": "Intégration Bouton WhatsApp Direct & Conversion Client", "amount": 10000})
            total += 10000
        if "express_24h" in options:
            items.append({"description": "Option Livraison Express Garantie en 24h-48h", "amount": 15000})
            total += 15000
        if "domain_hosting" in options:
            items.append({"description": "Nom de Domaine Personnalisé (.ci, .sn, .com) + Hébergement Sécurisé (1 An)", "amount": 25000})
            total += 25000
        if "catalog_products" in options:
            items.append({"description": "Section Catalogue Produits/Services Interactif (jusqu'à 10 articles)", "amount": 20000})
            total += 20000
        if "seo_pro" in options:
            items.append({"description": "Pack SEO Avancé (Référencement Google Maps + Mots-clés locaux)", "amount": 15000})
            total += 15000

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        insert_order({
            "id": ref_id,
            "invoice_number": invoice_num,
            "created_at": now_str,
            "company_name": data.get("company_name", "N/A"),
            "sector": data.get("sector", "N/A"),
            "whatsapp": data.get("whatsapp", "N/A"),
            "email": data.get("email", "N/A"),
            "city_country": data.get("city_country", "Abidjan, Côte d'Ivoire"),
            "options": options,
            "items": items,
            "total_fcfa": total,
            "status": "EN_ATTENTE_DE_PAIEMENT",
            "payment_status": "EN_ATTENTE_DE_PAIEMENT",
            "project_status": "NON_DEMARRE"
        })

        brief_record = {
            "id": ref_id,
            "invoice_number": invoice_num,
            "created_at": now_str,
            "company_name": data.get("company_name", "N/A"),
            "sector": data.get("sector", "N/A"),
            "whatsapp": data.get("whatsapp", "N/A"),
            "city_country": data.get("city_country", "Abidjan, Côte d'Ivoire"),
            "items": items,
            "total_fcfa": total,
            "status": "EN_ATTENTE_DE_PAIEMENT"
        }

        with open(os.path.join(BRIEFS_DIR, f"brief_{ref_id}.json"), "w", encoding="utf-8") as f:
            json.dump(brief_record, f, ensure_ascii=False, indent=2)
        with open(os.path.join(INVOICES_DIR, f"invoice_{ref_id}.json"), "w", encoding="utf-8") as f:
            json.dump(brief_record, f, ensure_ascii=False, indent=2)

        self.send_json({
            "success": True,
            "message": "Brief enregistré et commande créée.",
            "data": brief_record
        })

    def handle_payment_simulation(self, data):
        ref_id = data.get("id")
        method = data.get("payment_method", "Orange Money")
        phone = data.get("phone", "")
        tx_id = f"CNP-{uuid.uuid4().hex[:10].upper()}"
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        row = update_order(ref_id, {
            "status": "PAYE",
            "payment_status": "PAYE",
            "payment_method": method,
            "payment_phone": phone,
            "transaction_id": tx_id,
            "paid_at": now_str
        })

        if row:
            record = order_response(row)

            with open(os.path.join(INVOICES_DIR, f"invoice_{ref_id}.json"), "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

            self.send_json({
                "success": True,
                "message": f"Paiement de {record['total_fcfa']:,} FCFA validé via {method} !",
                "transaction_id": tx_id,
                "data": record
            })
        else:
            self.send_json({"error": "Commande introuvable dans la BDD"}, status=404)

    def handle_cinetpay_webhook(self, data):
        # Webhook IPN Listener for Live CinetPay Integration
        cpay_trans_id = data.get("cpay_trans_id") or data.get("transaction_id")
        cpay_status = data.get("status") or data.get("cpay_status")

        if cpay_trans_id and cpay_status in ["ACCEPTED", "SUCCES", "SUCCESS", "PAYE"]:
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            row = get_order(cpay_trans_id)
            if row is None and STORE.enabled:
                matches = STORE.select(f"?invoice_number=eq.{urllib.parse.quote(cpay_trans_id, safe='')}&limit=1")
                row = matches[0] if matches else None
            if row is not None:
                order_id = row["id"] if isinstance(row, sqlite3.Row) else row["id"]
                update_order(order_id, {
                    "status": "PAYE",
                    "payment_status": "PAYE",
                    "paid_at": now_str,
                    "transaction_id": cpay_trans_id
                })

        self.send_json({"status": "OK", "message": "Notification IPN CinetPay recue avec succes."})

    def handle_get_orders(self):
        refresh_project_statuses()
        orders = [order_response(row) for row in list_orders()]
        self.send_json({"success": True, "orders": orders})

    def handle_update_status(self, data):
        ref_id = data.get("id")
        new_status = data.get("project_status") or data.get("status")
        allowed = {"NON_DEMARRE", "EN_COURS", "LIVRE", "PROBLEME"}
        if new_status not in allowed:
            self.send_json({"error": "Statut de projet invalide"}, status=400)
            return
        previous = get_order(ref_id)
        row = update_order(ref_id, {"project_status": new_status, "status": new_status})
        if row and previous:
            old_order = order_response(previous)
            notification = {"email_sent": False, "reason": "Statut inchangé"}
            if old_order.get("project_status") != new_status:
                notification = send_client_notification(order_response(row), project_status_message(new_status))
            self.send_json({"success": True, "message": "Statut du projet mis à jour.", "notification": notification, "data": order_response(row)})
        else:
            self.send_json({"error": "Commande introuvable"}, status=404)

    def handle_chat(self, data):
        message = data.get("message", "").lower()
        if any(w in message for w in ["prix", "tarif", "combien", "coût", "cout", "budget"]):
            reply = "Chez **Landigo Express**, nos prix sont adaptés sur-mesure ! Le tarif de base démarre à **45 000 FCFA**. Remplissez notre formulaire pour générer votre facture pro-forma instantanée."
        elif any(w in message for w in ["paiement", "paye", "mobile money", "orange", "mtn", "wave", "moov", "cinetpay"]):
            reply = "Paiement 100% sécurisé via **CinetPay** (Orange Money, Wave, MTN MoMo, Moov Money)."
        elif any(w in message for w in ["délai", "delai", "temps", "durée", "duree", "express", "quand"]):
            reply = "Livraison garantie en **48h chrono** !"
        else:
            reply = "Bonjour ! Je suis **Landigo Bot**. Comment puis-je vous accompagner pour booster la visibilité de votre entreprise sur landigo-express.com ?"
        self.send_json({"success": True, "reply": reply})

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    print(f"--- SERVEUR LANDIGO EXPRESS (PRODUCTION READY) SUR http://localhost:{PORT} ---")
    try:
        with socketserver.TCPServer(("", PORT), LandigoHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Erreur port {PORT}: {e}")

if __name__ == "__main__":
    run_server()
