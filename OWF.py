import requests
import socket
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
import time
import random
import ipaddress
import os
import warnings
import urllib3

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
warnings.simplefilter('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

requests.packages.urllib3.disable_warnings()

THREADS = 10000
TIMEOUT = 2

class WebsiteFinder:
    def __init__(self):
        self.found_count = 0
        self.checked_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        self.protocols = ["HTTP", "HTTPS"]
        self.title_filter = None
        self.server_filter = None
        self.min_size = None
        self.max_size = None
        
        self.invalid_ranges = [
            ipaddress.ip_network('0.0.0.0/8'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('127.0.0.0/8'),
            ipaddress.ip_network('169.254.0.0/16'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16'),
            ipaddress.ip_network('224.0.0.0/4'),
            ipaddress.ip_network('240.0.0.0/4'),
        ]

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("Website Finder - Main Menu")
        print("=" * 50)
        print("1. Quick Start (Scan All)")
        print("2. Advanced Configuration")
        print("3. Exit")
        return input("\nSelect an option: ")

    def configure_advanced(self):
        self.clear_screen()
        print("Advanced Configuration\n")

        print("\nProtocol Selection:")
        print("1. HTTP only")
        print("2. HTTPS only")
        print("3. Both HTTP and HTTPS")
        proto_choice = input("Choose protocol option (1-3): ")
        if proto_choice == "1":
            self.protocols = ["HTTP"]
        elif proto_choice == "2":
            self.protocols = ["HTTPS"]
        else:
            self.protocols = ["HTTP", "HTTPS"]

        print("\nTitle Filter:")
        title_choice = input("Enter words to search in titles (e.g. 'blog shop' finds titles with blog or shop) (Enter for all): ").strip()
        self.title_filter = title_choice if title_choice else None

        print("\nServer Filter:")
        server_choice = input("Enter server type to search for (e.g., nginx, apache) (press Enter for all): ").strip()
        self.server_filter = server_choice.lower() if server_choice else None

        print("\nSize Limits (in bytes):")
        try:
            min_size = input("Enter minimum size (press Enter for no minimum): ").strip()
            self.min_size = int(min_size) if min_size else None
            max_size = input("Enter maximum size (press Enter for no maximum): ").strip()
            self.max_size = int(max_size) if max_size else None
        except ValueError:
            print("Invalid size values, using no size limits.")
            self.min_size = None
            self.max_size = None

        print("\nConfiguration saved! Press Enter to start scanning...")
        input()

    def matches_filters(self, result):
        """Check if a result matches all configured filters."""
        if result is None:
            return False

        if result['protocol'] not in self.protocols:
            return False

        if self.title_filter:
            title_words = self.title_filter.lower().split()
            result_title = result['title'].lower()
            if not any(word in result_title for word in title_words):
                return False

        if self.server_filter and self.server_filter not in result['server'].lower():
            return False

        if self.min_size and result['content_length'] < self.min_size:
            return False
        if self.max_size and result['content_length'] > self.max_size:
            return False

        return True

    def is_valid_ip(self, ip):
        """Check if IP is in valid range."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return not any(ip_obj in network for network in self.invalid_ranges)
        except ValueError:
            return False

    def generate_random_ip(self):
        """Generate a random IP address, avoiding invalid ranges."""
        while True:
            first = random.randint(1, 223)
            if first in [10, 127, 169, 172, 192]:
                continue
            second = random.randint(0, 255)
            third = random.randint(0, 255)
            fourth = random.randint(1, 254)
            
            ip = f"{first}.{second}.{third}.{fourth}"
            if self.is_valid_ip(ip):
                return ip

    def check_website(self, ip):
        """Check if an IP hosts a website."""
        try:
            for protocol in self.protocols:
                try:
                    session = requests.Session()
                    if protocol == "HTTPS":
                        session.verify = False
                        session.trust_env = False
                    
                    url = f"{protocol.lower()}://{ip}"
                    response = session.get(url, timeout=TIMEOUT)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if not ('text/html' in content_type or 'application/xhtml' in content_type):
                            continue

                        title = "No title found"
                        try:
                            import re
                            title_match = re.search('<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
                            if title_match:
                                title = title_match.group(1).strip()
                        except:
                            pass

                        result = {
                            'ip': ip,
                            'protocol': protocol,
                            'status_code': response.status_code,
                            'title': title,
                            'server': response.headers.get('Server', 'Unknown'),
                            'content_type': content_type,
                            'content_length': len(response.content),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                        if self.matches_filters(result):
                            return result

                except requests.RequestException:
                    continue
                except Exception as e:
                    continue
                finally:
                    if 'session' in locals():
                        session.close()

            return None

        except Exception as e:
            return None

    def save_result(self, result):
        """Save a single result to file."""
        with open('found_websites.txt', 'a') as f:
            f.write(f"\nFound at {result['timestamp']}\n")
            f.write(f"IP: {result['ip']}\n")
            f.write(f"Protocol: {result['protocol']}\n")
            f.write(f"Title: {result['title']}\n")
            f.write(f"Server: {result['server']}\n")
            f.write(f"Size: {result['content_length']} bytes\n")
            f.write("-" * 50 + "\n")

    def print_stats(self):
        """Print current statistics."""
        elapsed_time = time.time() - self.start_time
        ips_per_second = self.checked_count / elapsed_time if elapsed_time > 0 else 0
        print(f"\rChecked: {self.checked_count} | Found: {self.found_count} | Speed: {ips_per_second:.2f} IPs/s", end='')

    def worker(self):
        """Worker function for each thread."""
        while True:
            ip = self.generate_random_ip()
            result = self.check_website(ip)
            
            with self.lock:
                self.checked_count += 1
                if result:
                    self.found_count += 1
                    self.save_result(result)
                    print(f"\nFound website: {result['ip']} - {result['title']}")
                
                if self.checked_count % 10 == 0:
                    self.print_stats()

    def show_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("Website Finder - Main Menu")
        print("=" * 50)
        print("1. Quick Start (Scan All)")
        print("2. Advanced Configuration")
        print("3. View Found Websites")
        print("4. Exit")
        return input("\nSelect an option: ")

    def run(self):
        while True:
            choice = self.show_menu()
            
            if choice == "1":
                break
            elif choice == "2":
                self.configure_advanced()
                break
            elif choice == "3":
                from website_viewer import show_viewer
                show_viewer()
                continue
            elif choice == "4":
                print("Exiting...")
                return
            else:
                print("Invalid choice. Press Enter to continue...")
                input()
                continue

        self.clear_screen()
        print(f"Starting website finder with {THREADS} threads...")
        print("Current filters:")
        print(f"Protocols: {', '.join(self.protocols)}")
        if self.title_filter:
            print(f"Title filter: {self.title_filter}")
        if self.server_filter:
            print(f"Server filter: {self.server_filter}")
        if self.min_size or self.max_size:
            print(f"Size limits: {self.min_size or 'None'} - {self.max_size or 'None'} bytes")
        print("\nPress Ctrl+C to stop\n")
        
        with open('found_websites.txt', 'w') as f:
            f.write(f"Website Finder Started at {datetime.now()}\n")
            f.write("=" * 50 + "\n")

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            try:
                futures = [executor.submit(self.worker) for _ in range(THREADS)]
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                print("\n\nStopping... Please wait for threads to finish...")
                executor.shutdown(wait=True)
                print(f"\nFinal results: Checked {self.checked_count} IPs, found {self.found_count} websites")
                print("Results saved to 'found_websites.txt'")

if __name__ == "__main__":
    finder = WebsiteFinder()
    finder.run()
