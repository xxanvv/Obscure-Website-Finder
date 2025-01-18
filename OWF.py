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

# turn off all the annoying warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
warnings.simplefilter('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# disable ssl warnings - they're not important for this
requests.packages.urllib3.disable_warnings()

# main settings
THREADS = 10000  # how many threads to run at once
TIMEOUT = 2      # how long to wait before giving up on a request

class WebsiteFinder:
    def __init__(self):
        self.found_count = 0      # keeps track of how many sites we found
        self.checked_count = 0    # keeps track of how many ips we checked
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # stuff we'll set through the menu later
        self.protocols = ["HTTP", "HTTPS"]
        self.title_filter = None
        self.server_filter = None
        self.min_size = None
        self.max_size = None
        
        # ips we don't want to check (private/reserved ranges)
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
        # clears the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("website finder - main menu")
        print("=" * 50)
        print("1. quick start (scan everything)")
        print("2. advanced settings")
        print("3. exit")
        return input("\npick an option: ")

    def configure_advanced(self):
        self.clear_screen()
        print("advanced settings\n")

        # let user pick which protocols to use
        print("\nwhich protocols do you want to check:")
        print("1. just http")
        print("2. just https")
        print("3. both http and https")
        proto_choice = input("pick 1-3: ")
        if proto_choice == "1":
            self.protocols = ["HTTP"]
        elif proto_choice == "2":
            self.protocols = ["HTTPS"]
        else:
            self.protocols = ["HTTP", "HTTPS"]

        # filter by words in the title
        print("\nfilter by title:")
        title_choice = input("enter words to look for in titles (like 'blog shop') or press enter for all: ").strip()
        self.title_filter = title_choice if title_choice else None

        # filter by server type
        print("\nfilter by server:")
        server_choice = input("what server type to look for (like nginx or apache) or press enter for all: ").strip()
        self.server_filter = server_choice.lower() if server_choice else None

        # set size limits
        print("\nsize limits (in bytes):")
        try:
            min_size = input("minimum size (press enter for no min): ").strip()
            self.min_size = int(min_size) if min_size else None
            max_size = input("maximum size (press enter for no max): ").strip()
            self.max_size = int(max_size) if max_size else None
        except ValueError:
            print("those weren't valid numbers, not using size limits")
            self.min_size = None
            self.max_size = None

        print("\nall set! press enter to start scanning...")
        input()

    def matches_filters(self, result):
        # checks if a website matches what we're looking for
        if result is None:
            return False

        # check if protocol matches
        if result['protocol'] not in self.protocols:
            return False

        # check if title contains any of our keywords
        if self.title_filter:
            title_words = self.title_filter.lower().split()
            result_title = result['title'].lower()
            if not any(word in result_title for word in title_words):
                return False

        # check if it's running the server we want
        if self.server_filter and self.server_filter not in result['server'].lower():
            return False

        # check if size is in our range
        if self.min_size and result['content_length'] < self.min_size:
            return False
        if self.max_size and result['content_length'] > self.max_size:
            return False

        return True

    def is_valid_ip(self, ip):
        # makes sure ip isn't in any private/reserved ranges
        try:
            ip_obj = ipaddress.ip_address(ip)
            return not any(ip_obj in network for network in self.invalid_ranges)
        except ValueError:
            return False

    def generate_random_ip(self):
        # makes a random ip that's not in private/reserved ranges
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
        # tries to find a website at this ip
        try:
            for protocol in self.protocols:
                try:
                    # set up the request
                    session = requests.Session()
                    if protocol == "HTTPS":
                        session.verify = False
                        session.trust_env = False
                    
                    url = f"{protocol.lower()}://{ip}"
                    response = session.get(url, timeout=TIMEOUT)
                    
                    if response.status_code == 200:
                        # check if it's actually html
                        content_type = response.headers.get('Content-Type', '')
                        if not ('text/html' in content_type or 'application/xhtml' in content_type):
                            continue

                        # try to get the page title
                        title = "no title found"
                        try:
                            import re
                            title_match = re.search('<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
                            if title_match:
                                title = title_match.group(1).strip()
                        except:
                            pass

                        # save everything we found
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
        # saves what we found to a file
        with open('found_websites.txt', 'a') as f:
            f.write(f"\nfound at {result['timestamp']}\n")
            f.write(f"ip: {result['ip']}\n")
            f.write(f"protocol: {result['protocol']}\n")
            f.write(f"title: {result['title']}\n")
            f.write(f"server: {result['server']}\n")
            f.write(f"size: {result['content_length']} bytes\n")
            f.write("-" * 50 + "\n")

    def print_stats(self):
        # shows how we're doing so far
        elapsed_time = time.time() - self.start_time
        ips_per_second = self.checked_count / elapsed_time if elapsed_time > 0 else 0
        print(f"\rchecked: {self.checked_count} | found: {self.found_count} | speed: {ips_per_second:.2f} ips/s", end='')

    def worker(self):
        # what each thread does
        while True:
            ip = self.generate_random_ip()
            result = self.check_website(ip)
            
            with self.lock:
                self.checked_count += 1
                if result:
                    self.found_count += 1
                    self.save_result(result)
                    print(f"\nfound website: {result['ip']} - {result['title']}")
                
                if self.checked_count % 10 == 0:
                    self.print_stats()

    def show_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("website finder - main menu")
        print("=" * 50)
        print("1. quick start (scan everything)")
        print("2. advanced settings")
        print("3. website viewer")
        print("4. quit")
        return input("\npick an option: ")

    def run(self):
        while True:
            choice = self.show_menu()
            
            if choice == "1":
                # just start scanning with default settings
                break
            elif choice == "2":
                # let user change settings first
                self.configure_advanced()
                break
            elif choice == "3":
                # show what we found
                from website_viewer import show_viewer
                show_viewer()
                continue
            elif choice == "4":
                print("bye!")
                return
            else:
                print("that's not a valid option. press enter to try again...")
                input()
                continue

        self.clear_screen()
        print(f"starting up with {THREADS} threads...")
        print("current settings:")
        print(f"protocols: {', '.join(self.protocols)}")
        if self.title_filter:
            print(f"looking for titles with: {self.title_filter}")
        if self.server_filter:
            print(f"looking for servers running: {self.server_filter}")
        if self.min_size or self.max_size:
            print(f"size range: {self.min_size or 'any'} - {self.max_size or 'any'} bytes")
        print("\npress ctrl+c to stop\n")
        
        with open('found_websites.txt', 'w') as f:
            f.write(f"started scanning at {datetime.now()}\n")
            f.write("=" * 50 + "\n")

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            try:
                futures = [executor.submit(self.worker) for _ in range(THREADS)]
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                print("\n\nstopping... waiting for threads to finish...")
                executor.shutdown(wait=True)
                print(f"\nall done! checked {self.checked_count} ips, found {self.found_count} websites")
                print("everything is saved in 'found_websites.txt'")

if __name__ == "__main__":
    finder = WebsiteFinder()
    finder.run()