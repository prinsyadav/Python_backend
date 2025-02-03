
from flask import Flask, request, jsonify, render_template
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
# CORS(app, origins="*")  # Allow CORS for all domains (for testing only)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://prince-ai-app-seven.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Load API Key from environment variables (HIGHLY RECOMMENDED)
API_KEY = os.environ.get("GEMINI_API_KEY")

# Print API key for debugging (remove in production)
# print(f"API Key (DEBUG ONLY): {API_KEY}")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"


@app.route('/', methods=['GET'])  # Serve the HTML page
def index():
    return render_template('index.html')  # You'll create index.html


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    request_body = {
        "contents": [{
            "parts": [{
                "text": user_message
            }]
        }]
    }

    print(f"Request Body: {request_body}")

    try:
        response = requests.post(
            GEMINI_URL,
            json=request_body,
            headers={
                "Content-Type": "application/json"
            }
        )

        # Print response status and headers for debugging
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")

        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        print(f"Raw Gemini Response: {response_data}")

        if response_data.get("candidates") and response_data["candidates"][0].get("content"):
            ai_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            ai_response = "No valid response from Gemini."

        return jsonify({"response": ai_response})

    except requests.exceptions.RequestException as e:
        print(f"Gemini API Error: {e}")  # Print the error for debugging
        try:
            error_data = response.json()  # Attempt to parse error details
            print(f"Gemini API Error Details: {error_data}")
            error_message = error_data.get("error", {}).get("message", "Unknown error from Gemini API")

            return jsonify({"error": error_message}), response.status_code # Return error message and status code

        except ValueError:  # JSON decoding error
            return jsonify({"error": f"Gemini API Error: {e}"}), 500

    except (KeyError, IndexError) as e:
        print(f"Error parsing Gemini response: {e}")
        return jsonify({"error": "Error processing AI response"}), 500



@app.route('/api/set_api_key', methods=['POST'])  # For setting API key from frontend
def set_api_key():
    data = request.json
    new_api_key = data.get("api_key")

    if not new_api_key:
        return jsonify({"error": "API key is required"}), 400

    try:
        # In a real app, you'd store this securely (e.g., in a database or encrypted config file)
        # For this example, we'll just set it in the environment (less secure, but simpler)
        os.environ["GEMINI_API_KEY"] = new_api_key
        global API_KEY  # Use global to modify the module-level API_KEY
        API_KEY = new_api_key
        return jsonify({"message": "API key updated successfully"})
    except Exception as e:
        print(f"Error setting API key: {e}")
        return jsonify({"error": "Failed to set API key"}), 500


if __name__ == '__main__':
    app.run(debug=True)