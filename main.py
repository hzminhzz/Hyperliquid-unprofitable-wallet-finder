import requests
import json
import time
import os

# --- Configuration ---
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
# Add a small delay between requests to avoid being rate-limited
REQUEST_DELAY_S = 0.05 

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_pnl(user_address):
    """
    Fetches and calculates the cumulative PNL for a specific user address.
    The API returns a list of funding payments, so we sum the 'delta' of each.
    """
    payload = {
        "type": "userFunding",
        "user": user_address
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        funding_history = response.json()
        cumulative_pnl = 0.0
        
        # The response is a list of funding events. We need to sum the 'delta' from each.
        for payment in funding_history:
            cumulative_pnl += float(payment['delta'])
            
        return cumulative_pnl
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PNL for {user_address}: {e}")
        return None
    except (KeyError, IndexError, ValueError):
        # Handles cases where the response is empty or malformed
        print(f"Could not parse PNL data for {user_address}. User may have no funding history.")
        return None

def find_wallets():
    """
    Main function to find wallets based on user-defined PNL and balance criteria.
    """
    clear_screen()
    print("--- Hyperliquid Unprofitable Wallet Finder ---")
    
    # --- Get User Input ---
    try:
        min_pnl = float(input("Enter MINIMUM cumulative PNL (e.g., -50000): "))
        max_pnl = float(input("Enter MAXIMUM cumulative PNL (e.g., -1000): "))
        min_perp_balance = float(input("Enter MINIMUM current perp balance (USD, e.g., 100): "))
        max_perp_balance = float(input("Enter MAXIMUM current perp balance (USD, e.g., 5000): "))
    except ValueError:
        print("Invalid input. Please enter numbers only.")
        return

    print("\nFetching all user states... (This may take a moment)")

    try:
        # --- Step 1: Get the state of all users on the exchange ---
        payload = {"type": "clearinghouseState"}
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Fatal Error: Could not fetch clearinghouse state. {e}")
        return

    # Check if 'assetContexts' exists and is not empty
    if 'assetContexts' not in data or not data['assetContexts']:
        print("Could not find 'assetContexts' in the API response. Exiting.")
        return
        
    all_user_states = data['assetContexts'][0]['userStates']
    total_users = len(all_user_states)
    print(f"Found {total_users} active users. Now filtering...\n")

    found_wallets_count = 0
    
    # --- Step 2: Iterate through users and filter ---
    for i, user_state in enumerate(all_user_states):
        user_address = user_state['user']
        # Use 'totalRawUsd' from marginSummary as the perp balance
        perp_balance = float(user_state['marginSummary']['totalRawUsd'])
        
        # Print progress
        print(f"Scanning... [{i+1}/{total_users}]", end='\r')

        # --- Step 2a: EFFICIENTLY filter by balance FIRST ---
        if min_perp_balance <= perp_balance <= max_perp_balance:
            # --- Step 2b: If balance matches, THEN get the PNL (expensive call) ---
            time.sleep(REQUEST_DELAY_S) # Be respectful to the API
            cumulative_pnl = get_user_pnl(user_address)
            
            if cumulative_pnl is not None:
                # --- Step 2c: Check if the PNL is in the desired range ---
                if min_pnl <= cumulative_pnl <= max_pnl:
                    found_wallets_count += 1
                    print("\n" + "="*50)
                    print(f"✅ MATCH FOUND #{found_wallets_count}")
                    print(f"   Wallet Address: {user_address}")
                    print(f"   Cumulative PNL: ${cumulative_pnl:,.2f}")
                    print(f"   Current Balance: ${perp_balance:,.2f}")
                    print("="*50 + "\n")

    print(f"\nScan complete. Found {found_wallets_count} wallets matching your criteria.")

if __name__ == "__main__":
    find_wallets()
