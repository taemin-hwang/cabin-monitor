import subprocess
import time
from datetime import datetime

# Generate a timestamp for the filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"tcpdump_log_{timestamp}.txt"

# Prepare the tcpdump command
capture_command = ["tcpdump", "-i", "any", "udp port 50002", "-c", "10000", "-w", filename]

# Start the timer
start_time = time.time()

# Execute tcpdump command
subprocess.run(capture_command)

# End the timer and calculate elapsed time
end_time = time.time()
elapsed_time = end_time - start_time

fps = 10000 / elapsed_time

print(f"Time taken to capture 10000 packets: {elapsed_time} seconds")
print(f"Average FPS: {fps} fps")
print(f"Log saved in file: {filename}")
