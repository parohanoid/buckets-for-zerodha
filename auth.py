import os
import webbrowser
from dotenv import load_dotenv
from kiteconnect import KiteConnect


def get_kite_client() -> KiteConnect:
    load_dotenv()
    kite = KiteConnect(api_key=os.getenv("zerodha_api_key"))
    url  = kite.login_url()
    print(f"Opening login URL: {url}")
    if not webbrowser.open(url):
        print("Could not open browser automatically. Please open the URL above manually.")
    request_token = input("Paste the request_token from the redirect URL: ").strip()
    data = kite.generate_session(
        request_token=request_token,
        api_secret=os.getenv("zerodha_api_secret"),
    )
    kite.set_access_token(data["access_token"])
    return kite