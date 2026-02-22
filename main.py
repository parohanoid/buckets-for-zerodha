import logging
from kiteconnect import KiteConnect
from dotenv import load_dotenv
import os
import webbrowser
import json

def main():
    print("Excited to see you managing your own finances!")
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()

    kite = KiteConnect(api_key=os.getenv("zerodha_api_key"))

    url = kite.login_url()
    print(f"Attempting to open: {url}")
    if webbrowser.open(url):
        pass
    else:
        print("Failed to open URL automatically. Please open it manually.")

    print("Login to Kite on your Browser")

    request_token = input("Paste your request_token here from the URL on your browser: ")

    data = kite.generate_session(request_token=request_token, api_secret=os.getenv("zerodha_api_secret"))
    kite.set_access_token(data["access_token"])

    # Get mutual fund instruments
    with open("funds.json", "w") as json_file:
        json.dump(kite.mf_holdings(), json_file, indent=4)


if __name__ == "__main__":
    main()

