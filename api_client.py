import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RandomOrgClient:
    def __init__(self):
        self.api_key = os.getenv('RANDOM_API_KEY')
        self.base_url = "https://api.random.org/json-rpc/4/invoke"
    
    def generate_random_numbers(self, count=10, min_val=1, max_val=99):
        """Generate random numbers using Random.org API"""
        payload = {
            "jsonrpc": "2.0",
            "method": "generateIntegers",
            "params": {
                "apiKey": self.api_key,
                "n": count,
                "min": min_val,
                "max": max_val,
                "replacement": False  # Ensure unique numbers (no duplicates)
            },
            "id": 1
        }
        
        try:
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                return data["result"]["random"]["data"]
            else:
                raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Random.org API error: {str(e)}")

# Test function
if __name__ == "__main__":
    client = RandomOrgClient()
    try:
        numbers = client.generate_random_numbers()
        print(f"✅ Random.org API test successful!")
        print(f"Generated numbers: {numbers}")
    except Exception as e:
        print(f"❌ Random.org API test failed: {e}")