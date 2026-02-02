import time
import random
import logging
from config import LOG_FILE_PATH

# Configure logging to write to the SAME log file
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ACTIONS = [
    "User login successful",
    "Dashboard data loaded",
    "Email sent to user",
    "Report generated",
    "Payment processed",
    "Settings updated"
]

ERRORS = [
    "Database connection timeout",
    "Payment gateway 502 Bad Gateway",
    "NullPointerException in generate_report()",
    "API rate limit exceeded",
    "Disk space low (95%)"
]

print("🚀 Starting log generator...")
print(f"📝 Writing logs to: {LOG_FILE_PATH}")
print("Press Ctrl+C to stop.")

try:
    while True:
        if random.random() < 0.8:
            action = random.choice(ACTIONS)
            logging.info(f"Action: {action}")
            print(f"INFO: {action}")
        else:
            error = random.choice(ERRORS)
            logging.error(f"CRITICAL FAILURE: {error}")
            print(f"ERROR: {error}")

        time.sleep(random.uniform(0.5, 2.0))

except KeyboardInterrupt:
    print("\nLog generator stopped.")
