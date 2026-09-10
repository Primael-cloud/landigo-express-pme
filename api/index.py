import http.server
import json
import os
import sqlite3
import urllib.parse
import uuid
from datetime import datetime

try:
    from .supabase_client import (
        get_order as supabase_get_order,
        get_order_by_invoice as supabase_get_order_by_invoice,
        insert_order as supabase_insert_order,
        is_enabled as supabase_enabled,
        list_orders as supabase_list_orders,
        update_order as supabase_update_order,
    )
except ImportError:
    from supabase_client import (
        get_order as supabase_get_order,
        get_order_by_invoice as supabase_get_order_by_invoice,
        insert_order as supabase_insert_order,
        is_enabled as supabase_enabled,
        list_orders as supabase_list_orders,
        update_order as supabase_update_order,
    )

# In serverless environments (Vercel), writeable data goes to /tmp or remote DB (Supabase)
IS_VERCEL = os.environ.get('VERCEL', '0') == '1'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = "/tmp/data" if IS_VERCEL else os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "landigo.db")

os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
            payment_method TEXT,
            payment_phone TEXT,
            transaction_id TEXT,
            paid_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def order_response(row):
    if isinstance(row, sqlite3.Row):
        return {
            "id": row["id"],
            "invoice_number": row["invoice_number"],
            "created_at": row["created_at"],
            "company_name": row["company_name"],
            "sector": row["sector"],
            "whatsapp": row["whatsapp"],
            "city_country": row["city_country"],
            "options": json.loads(row["options_json"]) if row["options_json"] else [],
            "items": json.loads(row["items_json"]) if row["items_json"] else [],
            "total_fcfa": row["total_fcfa"],
            "status": row["status"],
            "payment_method": row["payment_method"],
            "payment_phone": row["payment_phone"],
            "transaction_id": row["transaction_id"],
            "paid_at": row["paid_at"]
        }

    return {
        "id": row.get("id"),
        "invoice_number": row.get("invoice_number"),
        "created_at": row.get("created_at"),
        "company_name": row.get("company_name"),
        "sector": row.get("sector"),
        "whatsapp": row.get("whatsapp"),
        "city_country": row.get("city_country"),
        "options": row.get("options_json", []),
        "items": row.get("items_json", []),
        "total_fcfa": row.get("total_fcfa"),
        "status": row.get("status"),
        "payment_method": row.get("payment_method"),
        "payment_phone": row.get("payment_phone"),
        "transaction_id": row.get("transaction_id"),
        "paid_at": row.get("paid_at")
    }


def insert_order(order):
    if supabase_enabled():
        supabase_insert_order({
            "id": order["id"],
            "invoice_number": order["invoice_number"],
            "created_at": order["created_at"],
            "company_name": order["company_name"],
            "sector": order["sector"],
            "whatsapp": order["whatsapp"],
            "email": order["email"],
            "city_country": order["city_country"],
            "options_json": order["options"],
            "items_json": order["items"],
            "total_fcfa": order["total_fcfa"],
            "status": order["status"]
        })
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (id, invoice_number, created_at, company_name, sector, whatsapp, email, city_country, options_json, items_json, total_fcfa, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order["id"], order["invoice_number"], order["created_at"], order["company_name"],
        order["sector"], order["whatsapp"], order["email"], order["city_country"],
        json.dumps(order["options"]), json.dumps(order["items"]), order["total_fcfa"], order["status"]
    ))
    conn.commit()
    conn.close()


def update_order(order_id, updates):
    if supabase_enabled():
        return supabase_update_order(order_id, updates)

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
    if supabase_enabled():
        return supabase_get_order(order_id)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def list_orders():
    if supabase_enabled():
        return supabase_list_orders()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

class handler(http.server.BaseHTTPRequestHandler):
    def send_image_file(self, filename):
        file_path = os.path.join(BASE_DIR, 'public', filename)
        try:
            with open(file_path, 'rb') as image_file:
                content = image_file.read()
        except OSError:
            self.send_json({"error": "Image introuvable"}, status=404)
            return

        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(content)

    def send_html_file(self, filename):
        file_path = os.path.join(BASE_DIR, filename)
        try:
            with open(file_path, 'rb') as html_file:
                content = html_file.read()
        except OSError:
            self.send_json({"error": "Page introuvable"}, status=404)
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def is_authenticated(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        expected_token = os.environ.get("TOKEN", "landigo_admin_token_2026")
        return token == expected_token

    def send_json(self, response_data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/logo.jpg':
            self.send_image_file('logo.jpg')
        elif parsed_url.path == '/':
            self.send_html_file('index.html')
        elif parsed_url.path in ('/admin-login', '/admin-login/'):
            self.send_html_file('admin_login.html')
        elif parsed_url.path in ('/admin', '/admin/'):
            self.send_html_file('admin.html')
        elif parsed_url.path == '/api/admin/orders':
            if not self.is_authenticated():
                self.send_json({"error": "Non autorise"}, status=401)
                return
            self.handle_get_orders()
        else:
            self.send_json({"message": "Landigo Express API Ready on Vercel"})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/admin/login':
            self.handle_admin_login(data)
        elif path == '/api/brief':
            self.handle_create_brief(data)
        elif path == '/api/chat':
            self.handle_chat(data)
        elif path == '/api/payment/simulate':
            self.handle_payment_simulation(data)
        elif path == '/api/cinetpay/notify':
            self.handle_cinetpay_webhook(data)
        elif path == '/api/admin/update_status':
            if not self.is_authenticated():
                self.send_json({"error": "Non autorise"}, status=401)
                return
            self.handle_update_status(data)
        else:
            self.send_json({'error': 'Endpoint non trouve'}, status=404)

    def handle_admin_login(self, data):
        u = data.get("username", "")
        p = data.get("password", "")
        expected_user = os.environ.get("ADMIN_USERNAME", "admin")
        expected_pass = os.environ.get("ADMIN_PASSWORD", "landigo2026!")
        expected_token = os.environ.get("TOKEN", "landigo_admin_token_2026")

        if u == expected_user and p == expected_pass:
            self.send_json({
                "success": True,
                "token": expected_token,
                "message": "Authentification réussie"
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

        try:
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
                "status": "EN_ATTENTE_DE_PAIEMENT"
            })
        except Exception as error:
            print(f"Erreur création commande: {error}")
            self.send_json({"error": f"Erreur Supabase: {error}"}, status=502)
            return

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
            "payment_method": method,
            "payment_phone": phone,
            "transaction_id": tx_id,
            "paid_at": now_str
        })

        if row:
            record = order_response(row)
            self.send_json({
                "success": True,
                "message": f"Paiement de {record['total_fcfa']:,} FCFA validé via {method} !",
                "transaction_id": tx_id,
                "data": record
            })
        else:
            self.send_json({"error": "Commande introuvable"}, status=404)

    def handle_cinetpay_webhook(self, data):
        cpay_trans_id = data.get("cpay_trans_id") or data.get("transaction_id")
        cpay_status = data.get("status") or data.get("cpay_status")

        if cpay_trans_id and cpay_status in ["ACCEPTED", "SUCCES", "SUCCESS", "PAYE"]:
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            row = get_order(cpay_trans_id)
            if row is None and supabase_enabled():
                row = supabase_get_order_by_invoice(cpay_trans_id)
            if row is not None:
                order_id = row["id"]
                update_order(order_id, {
                    "status": "PAYE",
                    "paid_at": now_str,
                    "transaction_id": cpay_trans_id
                })

        self.send_json({"status": "OK", "message": "Notification IPN CinetPay reçue."})

    def handle_get_orders(self):
        orders = [order_response(row) for row in list_orders()]
        self.send_json({"success": True, "orders": orders})

    def handle_update_status(self, data):
        ref_id = data.get("id")
        new_status = data.get("status")
        update_order(ref_id, {"status": new_status})
        self.send_json({"success": True, "message": "Statut mis à jour."})

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
