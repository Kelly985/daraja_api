from flask import Flask, jsonify, request
import requests
from base64 import b64encode
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
 
# Replace with your Daraja API credentials
consumer_key = "4hoJ8vIYbCnkpauEjqG0WltbKjxKTFEw"
consumer_secret = "uWZsoYAekHPsmh2D"
lipa_na_mpesa_online_passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
lipa_na_mpesa_online_shortcode = "174379"
lipa_na_mpesa_online_callback_url = "https://mydomain.com/path"

# Generate M-Pesa access token
# @app.route("/token", methods=["GET"])
def generate_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded_credentials = b64encode(credentials.encode()).decode("utf-8")
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

        try:
            data = response.json()
            access_token = data.get("access_token")

            if access_token:
                return {"access_token": access_token}
            else:
                return {"error": "Access token not found in the response"}

        except ValueError as ve:
            return {"error": f"Error parsing JSON response: {str(ve)}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# Lipa Na M-Pesa online payment function
def lipa_na_mpesa_online(access_token, amount, phone_number):
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "BusinessShortCode": lipa_na_mpesa_online_shortcode,
        "Password": b64encode(
            f"{lipa_na_mpesa_online_shortcode}{lipa_na_mpesa_online_passkey}{datetime.now().strftime('%Y%m%d%H%M%S')}".encode()
        ).decode("utf-8"),
        "Timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": lipa_na_mpesa_online_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": lipa_na_mpesa_online_callback_url,
        "AccountReference": "YourReference",
        "TransactionDesc": "Payment for services",
    }
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

# Flask route for initiating M-Pesa payment
@app.route("/pay", methods=["POST"])
def initiate_payment():
    try:
        data = request.get_json()
        amount = data.get("amount")
        phone_number = data.get("phone_number")

        if not amount or not phone_number:
            return jsonify({"error": "Missing required parameters"}), 400

        access_token_response = generate_access_token()
        
        if "error" in access_token_response:
            error_message = access_token_response.get("error", "Unknown error")
            raise ValueError(f"Error generating access token: {error_message}")

        access_token = access_token_response["access_token"]
        payment_response = lipa_na_mpesa_online(access_token, amount, phone_number)

        return jsonify(payment_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
