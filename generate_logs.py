import time
import random
import logging
from datetime import datetime

# Configure logging to write to a file
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# List of simulated actions and errors
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

print("Starting log generator... Writing to app.log")
print("Press Ctrl+C to stop.")

try:
    while True:
        # 80% chance of normal action, 20% chance of error
        if random.random() < 0.8:
            action = random.choice(ACTIONS)
            logging.info(f"Action: {action} | Duration: {random.randint(10, 500)}ms")
            print(f"Logged INFO: {action}")
        else:
            error = random.choice(ERRORS)
            logging.error(f"CRITICAL FAILURE: {error} | Trace ID: {random.randint(1000,9999)}")
            print(f"Logged ERROR: {error}")
        
        # specific delay to simulate real-time traffic (0.5 to 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))

except KeyboardInterrupt:
    print("\nLog generator stopped.")
