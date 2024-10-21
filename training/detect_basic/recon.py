import nmap
import sys
import logging

# Configure logging to console (stdout)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[logging.StreamHandler()])

def scan_industrial_ports(ip):
    # Create a PortScanner object
    nm = nmap.PortScanner()

    # Define the ports to scan: HTTP (80), Modbus (502), OPC UA (4840)
    ports_to_scan = '80,102, 502,4840, 20000, 44818'

    try:
        # Log the start of the scan
        logging.debug(f"Starting scan for IP: {ip} on ports 80, 102, 502, 4840, 20000, 44818")

        # Perform a version detection scan on the specified ports
        logging.debug(f"Scanning {ip} for HTTP, S7, Modbus, OPC UA, DNP3, and Ethernet/IP ports...")
        nm.scan(ip, ports_to_scan, arguments='-sV')

        # Check if any ports are open and print their details
        if nm.all_hosts():
            for host in nm.all_hosts():
                host_info = f"Host: {host} ({nm[host].hostname()})\nState: {nm[host].state()}"
                logging.debug(host_info)
                logging.debug(host_info)
                
                for proto in nm[host].all_protocols():
                    proto_info = f"\nProtocol: {proto}"
                    logging.debug(proto_info)
                    
                    ports = nm[host][proto].keys()
                    for port in sorted(ports):
                        port_info = nm[host][proto][port]
                        service_info = (f"Port: {port}\tState: {port_info['state']}\n"
                                        f"Service: {port_info['name']}\tVersion: {port_info.get('version', 'Unknown')}")
                        logging.debug(service_info)
        else:
            msg = f"No information found for IP {ip}"
            logging.warning(msg)

    except nmap.PortScannerError as e:
        error_msg = f"Nmap error: {e}"
        logging.debug(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        logging.debug(error_msg)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python3 recon.py <IP Address of the Target>")
        sys.exit(1)
    
    # Get the IP address from the command-line arguments
    ip_address = sys.argv[1]

    # Run the scan
    logging.info("Recon started")
    scan_industrial_ports(ip_address)
    logging.info("Recon finished")
