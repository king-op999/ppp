from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# --- Configuration ---
HALFBLOOD_URL = "https://halfblood.famapp.in/vpa/verifyExt"
RAZORPAY_IFSC_URL = "https://ifsc.razorpay.com/"
HEADERS = {
    'User-Agent': "A015 | Android 15 | Dalvik/2.1.0 | Tetris | 318D0D6589676E17F88CCE03A86C2591C8EBAFBA |  (Build -1) | 3DB5HIEMMG",
    'Accept': "application/json",
    'Content-Type': "application/json",
    'authorization': "Token eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiZXBrIjp7Imt0eSI6Ik9LUCIsImNydiI6Ilg0NDgiLCJ4IjoiZldEV2hlWTRyUXZRdzJQT0NCWWJpcFN6ZmJaczFPZFktWGcwZ25ORFV4VDVVNnV3TjhCLUw0Rm9PU1JQMGhKWVoyX1FiTnJqQ0s0In0sImFsZyI6IkVDREgtRVMifQ..YomDRfMtMXcQvvY5zqo1Rw.hgxy4MfXnzkqq8Xc31sYov9ggEovQJ7CebQnmeQ1RnyJBy52kHi_1kcEwX82oYZIuQaZ8FFSqIqCoIxrVJrqQflHF_ZjaU4lhwcoAV-l2_9vMjMe31FpZ9iXe56SxIGi3wEIDDyMnzWYW8N41An_srXEXj-y5nI-p1k4NEh_Ld0QwtLW4oR0NWJjySEhaeJy09H3EEZ9paJmlJPK2fKpaQ0k7eBKq6Ltib_l7kMmSJ5V7qnl5FX20mz-0IjkSa3BIOvfrkQg_TrzjzGg3l7B7g.QdQj098-_lKf08lxXEL3raDrj6gHHEYQjMAJ_7W1mPo"
}

# ✅ API Keys
ALLOWED_KEYS = {
    "notfirnkanshs": "Free User",
    "456": "Premium User",
    "keyNever019191": "Admin"
}

# ============================================
# 🔑 KEY CHECK
# ============================================
def check_api_key(req):
    api_key = req.headers.get("x-api-key") or req.args.get("key")
    if not api_key:
        return False, "Missing API key"
    if api_key not in ALLOWED_KEYS:
        return False, "Invalid API key"
    return True, ALLOWED_KEYS[api_key]

# ============================================
# 🔍 MAIN FUNCTION
# ============================================
def fetch_and_chain(upi_id):
    """Fetch UPI details from FamPay + IFSC from Razorpay"""
    
    # Step 1: FamPay API
    vpa_payload = {"upi_string": f"upi://pay?pa={upi_id}"}
    vpa_details = None
    ifsc_code = None
    
    try:
        response_vpa = requests.post(
            HALFBLOOD_URL,
            data=json.dumps(vpa_payload),
            headers=HEADERS,
            timeout=15
        )
        response_vpa.raise_for_status()
        vpa_info = response_vpa.json().get("data", {}).get("verify_vpa_resp", {})
        
        if not vpa_info:
            return {"status": "error", "message": "UPI details not found"}, 400

        vpa_details = {
            "name": vpa_info.get("name"),
            "vpa": vpa_info.get("vpa"),
            "ifsc": vpa_info.get("ifsc")
        }
        ifsc_code = vpa_details.get("ifsc")
    
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"FamPay API failed: {str(e)}"}, 500

    # Step 2: Razorpay IFSC
    bank_details = None
    
    if ifsc_code:
        try:
            response_ifsc = requests.get(
                f"{RAZORPAY_IFSC_URL}{ifsc_code}",
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response_ifsc.status_code == 200:
                bank_details = response_ifsc.json()
            else:
                bank_details = {"warning": f"IFSC lookup failed: {response_ifsc.status_code}"}
        except:
            bank_details = {"warning": "IFSC API timeout"}

    # Step 3: Build response
    result = {
        "status": "success",
        "developer": "@BRONX_ULTRA",
        "powered_by": "BRONX UPI API",
        "upi_id": upi_id,
        "vpa_details": vpa_details,
        "bank_details": bank_details
    }
    
    return result, 200

# ============================================
# 🛣️ ROUTES
# ============================================
@app.route('/')
def home():
    return jsonify({
        "service": "🏦 BRONX ULTRA UPI API",
        "version": "5.0",
        "source": "FamPay + Razorpay IFSC",
        "accuracy": "100% Real Data",
        "endpoints": {
            "lookup": "/api/upi?upi=username@handle&key=YOUR_KEY"
        },
        "example": "/api/upi?upi=test@ybl&key=456",
        "developer": "@BRONX_ULTRA"
    })

@app.route("/api/upi", methods=["GET"])
def api_upi_lookup():
    # Check API key
    is_valid, message = check_api_key(request)
    if not is_valid:
        return jsonify({"status": "error", "message": message, "developer": "@BRONX_ULTRA"}), 403

    upi_id = request.args.get("upi_id") or request.args.get("upi")
    if not upi_id:
        return jsonify({
            "status": "error",
            "message": "Missing UPI ID! Use: /api/upi?upi=name@handle&key=YOUR_KEY",
            "developer": "@BRONX_ULTRA"
        }), 400

    result, status = fetch_and_chain(upi_id)
    
    # Pretty print
    return app.response_class(
        response=json.dumps(result, indent=2, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "source": "FamPay + Razorpay",
        "developer": "@BRONX_ULTRA"
    })

# ============================================
# 🚀 MAIN
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
