# File: ping_checker.py

import requests
import argparse
import sys
import time

# --- Constants ---
TIMEOUT = 20  # seconds

def check_url_liveliness(url: str):
    """
    Performs a simple, credential-less GET request to a URL.

    Exits with code 0 on success (HTTP 2xx).
    Exits with code 1 on any failure (network error, timeout, non-2xx status).
    """
    print(f"Pinging URL: {url}...")
    start_time = time.time()
    try:
        # Use a common user-agent and allow redirects, which is typical for login pages.
        headers = {
            "User-Agent": "GitHub-Actions-Liveliness-Check/1.0"
        }
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=True, headers=headers)

        duration = time.time() - start_time
        print(f"Response from {url} in {duration:.2f}s. Status Code: {response.status_code}")

        # raise_for_status() will raise an HTTPError for 4xx or 5xx status codes.
        response.raise_for_status()

        print(f"✅ SUCCESS: {url} is live and responding correctly.")
        # A zero exit code signals success to the shell/GitHub Actions runner.
        sys.exit(0)

    except requests.exceptions.Timeout as e:
        print(f"❌ FAILURE: Timeout after {TIMEOUT} seconds for {url}. Error: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        # This catches connection errors, HTTP errors (from raise_for_status), etc.
        print(f"❌ FAILURE: Could not reach {url}. Error: {e}")
        # A non-zero exit code signals failure.
        sys.exit(1)
    except Exception as e:
        print(f"❌ FAILURE: An unexpected error occurred for {url}. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A simple script to check if a URL is live and returns a 2xx status code."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="The full URL of the environment login page to check."
    )
    args = parser.parse_args()

    check_url_liveliness(args.url)
