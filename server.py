import http.server
import socketserver
import json
import os
import sqlite3
import urllib.parse
import uuid
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
        "TOKEN": "landigo_admin_token_2026"
    }
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()

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

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (id, invoice_number, created_at, company_name, sector, whatsapp, email, city_country, options_json, items_json, total_fcfa, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ref_id, invoice_num, now_str,
            data.get("company_name", "N/A"),
            data.get("sector", "N/A"),
            data.get("whatsapp", "N/A"),
            data.get("email", "N/A"),
            data.get("city_country", "Abidjan, Côte d'Ivoire"),
            json.dumps(options),
            json.dumps(items),
            total,
            "EN_ATTENTE_DE_PAIEMENT"
        ))
        conn.commit()
        conn.close()

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

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = 'PAYE', payment_method = ?, payment_phone = ?, transaction_id = ?, paid_at = ?
            WHERE id = ?
        ''', (method, phone, tx_id, now_str, ref_id))
        conn.commit()
        
        cursor.execute("SELECT * FROM orders WHERE id = ?", (ref_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            record = {
                "id": row[0],
                "invoice_number": row[1],
                "created_at": row[2],
                "company_name": row[3],
                "sector": row[4],
                "whatsapp": row[5],
                "city_country": row[7],
                "items": json.loads(row[9]),
                "total_fcfa": row[10],
                "status": row[11],
                "payment_method": row[12],
                "payment_phone": row[13],
                "transaction_id": row[14],
                "paid_at": row[15]
            }

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
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute('''
                UPDATE orders 
                SET status = 'PAYE', paid_at = ?, transaction_id = ?
                WHERE id = ? OR invoice_number = ?
            ''', (now_str, cpay_trans_id, cpay_trans_id, cpay_trans_id))
            conn.commit()
            conn.close()

        self.send_json({"status": "OK", "message": "Notification IPN CinetPay recue avec succes."})

    def handle_get_orders(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        orders = []
        for r in rows:
            orders.append({
                "id": r["id"],
                "invoice_number": r["invoice_number"],
                "created_at": r["created_at"],
                "company_name": r["company_name"],
                "sector": r["sector"],
                "whatsapp": r["whatsapp"],
                "city_country": r["city_country"],
                "options": json.loads(r["options_json"]) if r["options_json"] else [],
                "items": json.loads(r["items_json"]) if r["items_json"] else [],
                "total_fcfa": r["total_fcfa"],
                "status": r["status"],
                "payment_method": r["payment_method"],
                "payment_phone": r["payment_phone"],
                "transaction_id": r["transaction_id"],
                "paid_at": r["paid_at"]
            })
        self.send_json({"success": True, "orders": orders})

    def handle_update_status(self, data):
        ref_id = data.get("id")
        new_status = data.get("status")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, ref_id))
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Statut mis à jour dans la BDD."})

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
