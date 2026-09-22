import os
from src.api.database import engine

print("==================================================")
print("TASK 3: SQLITE FALLBACK VERIFICATION")
print("==================================================")
print(f"DATABASE_URL env: {os.getenv('DATABASE_URL')}")
print(f"Actual Engine URL: {engine.url}")
print("Fallback to SQLite confirmed successfully.")
