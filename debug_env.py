import os
import sys

print("--- DEBUG ENV SCRIPT ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

# Check .env existence
if os.path.exists(".env"):
    print(".env file FOUND.")
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        print(f".env content length: {len(content)}")
        if "SLACK_WEBHOOK_URL" in content:
            print("SLACK_WEBHOOK_URL found in .env text.")
        else:
            print("SLACK_WEBHOOK_URL NOT found in .env text.")
else:
    print(".env file NOT FOUND.")

# Check Environment Variables
webhook = os.environ.get("SLACK_WEBHOOK_URL")
print(f"os.environ.get('SLACK_WEBHOOK_URL'): '{webhook}'")

# Print all SLACK variables
print("All SLACK_ variables:")
for k, v in os.environ.items():
    if "SLACK" in k:
        print(f"  {k}: {v}")

print("--- END DEBUG ---")
