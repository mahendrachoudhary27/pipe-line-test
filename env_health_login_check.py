import requests
import argparse
import sys
import time
import os
import json
import pytz
from pathlib import Path
from datetime import datetime
import threading

# Constants
PING_TIMEOUT = 20
LOGIN_TIMEOUT = 60

# Login endpoints fallback templates
LOGIN_URL_TEMPLATES = [
    "{url}/api/frontegg/identity/resources/auth/v1/user",
    "https://gs-erag.frontegg.com/frontegg/identity/resources/auth/v1/user"
]

def log_message(message):
    timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{timestamp}] [Thread-{threading.get_ident()}] {message}")

def check_url_liveliness(url):
    """Ping URL to see if it's live (2xx status)."""
    log_message(f"Pinging URL: {url}...")
    start_time = time.time()
    try:
        headers = { "User-Agent": "GitHub-Actions-Liveliness-Check/1.0" }
        response = requests.get(url, timeout=PING_TIMEOUT, allow_redirects=True, headers=headers)
        response.raise_for_status()
        duration = time.time() - start_time
        log_message(f"✅ SUCCESS: {url} responded in {duration:.2f}s with {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"❌ FAILURE: Could not reach {url}. Error: {e}")
        return False

def login_to_environment(url, email, password, application_id):
    payload = {
        "email": email,
        "password": password,
        "invitationToken": ""
    }
    session = requests.Session()
    last_error = None

    for login_url_template in LOGIN_URL_TEMPLATES:
        login_url = login_url_template.format(url=url)
        headers = {
            "Content-Type": "application/json",
            "frontegg-requested-application-id": str(application_id),
            "frontegg-source": "login-box",
            "User-Agent": "Mozilla/5.0"
        }

        log_message(f"Attempting login via: {login_url}")
        try:
            response = session.post(
                login_url,
                headers=headers,
                json=payload,
                timeout=LOGIN_TIMEOUT
            )
            response.raise_for_status()
            log_message("🎉 LOGIN SUCCESSFUL.")
            return session.cookies.get_dict()
        except requests.exceptions.HTTPError as err:
            log_message(f"Login failed with HTTP error: {err}")
            if err.response.status_code == 404:
                continue  # Try next fallback
            else:
                return None
        except Exception as e:
            log_message(f"Login error: {e}")
            continue

    log_message(f"❌ All login attempts failed. Last error: {last_error}")
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check liveliness of a URL and attempt login.")
    parser.add_argument("--url", required=True, help="Base environment URL (e.g., https://customer.gigaspaces.net)")
    args = parser.parse_args()

    # Load credentials from environment (ideal for GitHub Actions secrets)
    try:
        email = os.environ["EMAIL"]
        password = os.environ["PASSWORD"]
        application_id = os.environ.get("APPLICATION_ID", "1")  # default to "1" if not set
    except KeyError as e:
        log_message(f"🚫 Missing required environment variable: {e}")
        sys.exit(1)

    if check_url_liveliness(args.url):
        if login_to_environment(args.url, email, password, application_id):
            log_message("✅ LOGIN CHECK PASSED.")
            sys.exit(0)
        else:
            log_message("❌ LOGIN FAILED.")
            sys.exit(1)
    else:
        log_message("🛑 URL not live. Skipping login attempt.")
        sys.exit(1)
