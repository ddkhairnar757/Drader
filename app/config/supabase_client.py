from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("URL:", url)
print("KEY PREFIX:", key[:20] if key else "None")
print("KEY LENGTH:", len(key) if key else 0)

supabase = create_client(url, key)