import os
import requests
import pyotp
from bs4 import BeautifulSoup
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USERNAME = os.getenv("PA_USERNAME")
PASSWORD = os.getenv("PA_PASSWORD")
TOTP_SECRET = os.getenv("PA_TOTP_SECRET")

LOGIN_URL = "https://www.pythonanywhere.com/login/"
WEBAPP_URL = f"https://www.pythonanywhere.com/user/{USERNAME}/webapps/"
EXTEND_URL_TEMPLATE = "https://www.pythonanywhere.com/user/{USERNAME}/webapps/{USERNAME}.pythonanywhere.com/extend"

def main():
    if not USERNAME or not PASSWORD or not TOTP_SECRET:
        logging.error("Missing environment variables. PA_USERNAME, PA_PASSWORD, and PA_TOTP_SECRET are required.")
        sys.exit(1)

    session = requests.Session()
    
    # Set headers to mimic a real browser to avoid blocks
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # 1. Get initial login page to grab CSRF token
    logging.info("Accessing login page to retrieve CSRF token...")
    response = session.get(LOGIN_URL)
    
    if response.status_code != 200:
        logging.error(f"Failed to access login page. Status code: {response.status_code}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if not csrf_input:
        logging.error("Could not find CSRF token on login page.")
        sys.exit(1)
        
    csrf_token = csrf_input['value']

    # 2. Perform Login (Username & Password)
    logging.info("Attempting login...")
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'auth-username': USERNAME,
        'auth-password': PASSWORD,
        'login_view-current_step': 'auth'
    }

    response = session.post(LOGIN_URL, data=login_data, headers={'Referer': LOGIN_URL})
    
    # 3. Check for 2FA requirement
    if "two_factor" in response.url or "TOTP" in response.text or 'name="two_factor_auth-otp_token"' in response.text:
        logging.info("2FA required. Generating TOTP code...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            csrf_token = csrf_input['value']
            
        totp = pyotp.TOTP(TOTP_SECRET)
        otp_code = totp.now()
        logging.info(f"Generated OTP: {otp_code}")

        totp_data = {
            'csrfmiddlewaretoken': csrf_token,
            'two_factor_auth-otp_token': otp_code,
            'login_view-current_step': 'two_factor_auth'
        }
        
        response = session.post(response.url, data=totp_data, headers={'Referer': response.url})

    # Verify login success by accessing webapps page
    response = session.get(WEBAPP_URL)
    if "Log in" in response.text or USERNAME not in response.text:
         logging.error("Login failed. Please check your credentials or 2FA secret.")
         sys.exit(1)
         
    logging.info("Login successful!")

    # 4. Fetch the WebApp page to find the specific form to extend
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = session.cookies.get('csrftoken')
    
    if not csrf_token:
         logging.error("CSRF token missing after login.")
         sys.exit(1)

    extend_url = EXTEND_URL_TEMPLATE.format(USERNAME=USERNAME)
    logging.info(f"Attempting to extend webapp at {extend_url}...")
    
    # 5. Click the "Run until 3 months" button (POST request)
    extend_data = {
        'csrfmiddlewaretoken': csrf_token,
    }
    
    extend_response = session.post(
        extend_url, 
        data=extend_data, 
        headers={
            'Referer': WEBAPP_URL,
            'X-Requested-With': 'XMLHttpRequest' # Important for PA ajax requests
        }
    )

    if extend_response.status_code == 200:
        logging.info("✅ Successfully clicked 'Run until 1/3 months'. Webapp extended!")
    else:
        logging.error(f"Failed to extend webapp. Status code: {extend_response.status_code}")
        logging.error(extend_response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
