#!/usr/bin/env python3

import argparse
import time
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import sys
import threading
from termcolor import colored 

class EmailScrapper():

    def __init__(self):
        
        self.left_links = deque() # To store, extracted links and links left to scrap
        self.scrapped_emails = set() # To store extracted email
        self.visited_site = set() # To store scrapped site 

    def intro(self) -> str:
        """Returns Red logo."""

        logo = """
▓█████  ███▄ ▄███▓ ▄▄▄       ██▓ ██▓         ██████  ▄████▄   ██▀███   ▄▄▄       ██▓███   ██▓███  ▓█████  ██▀███  
▓█   ▀ ▓██▒▀█▀ ██▒▒████▄    ▓██▒▓██▒       ▒██    ▒ ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▓██░  ██▒▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒███   ▓██    ▓██░▒██  ▀█▄  ▒██▒▒██░       ░ ▓██▄   ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▓██░ ██▓▒▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒▓█  ▄ ▒██    ▒██ ░██▄▄▄▄██ ░██░▒██░         ▒   ██▒▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
░▒████▒▒██▒   ░██▒ ▓█   ▓██▒░██░░██████▒   ▒██████▒▒▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒██▒ ░  ░▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░░ ▒░ ░░ ▒░   ░  ░ ▒▒   ▓▒█░░▓  ░ ▒░▓  ░   ▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░▒▓▒░ ░  ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
 ░ ░  ░░  ░      ░  ▒   ▒▒ ░ ▒ ░░ ░ ▒  ░   ░ ░▒  ░ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░░▒ ░     ░▒ ░      ░ ░  ░  ░▒ ░ ▒░
   ░   ░      ░     ░   ▒    ▒ ░  ░ ░      ░  ░  ░  ░          ░░   ░   ░   ▒   ░░       ░░          ░     ░░   ░ 
   ░  ░       ░         ░  ░ ░      ░  ░         ░  ░ ░         ░           ░  ░                     ░  ░   ░     
                                                    ░         ~ N1XA-CLI
                                                    """
        
        return colored(logo, 'red')
        

    def is_visited(self, url:str) -> bool:
        """Returns True if url is already visited else returns False."""

        return url in self.visited_site
    
    def ext_emails(self, data:str) -> list:
        """Takes data as text and returns lists of emails."""

        return re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", data)

    def print_emails(self, found_email:list) -> None:
        
        print(colored(f"[+] Found {len(found_email)} Emails", 'green'))

        for email in found_email:
            print(colored(email, 'yellow'))

    def write_to(self, filename, emails:list) -> None:

        print(colored(f"[+] Writing to {filename}", 'yellow'))

        with open(filename, "w") as f:
            for email in emails:
                f.write(f"{email}\n")

    def scrap(self, session, base_domain, url) -> None:
        """Takes session, basedomain, a set of email and link"""

        try:
            print(colored(f"\r\033[K[+] Scrapping from: {url}", 'green'), flush=True, end="")

            r = session.get(url=url, timeout=2)
            r.raise_for_status()

            try:
                if (r.headers.get('Content-Type')).split(';')[0] != "text/html":
                    return
            except requests.RequestException:
                print(colored(f"\n[-] Cannot extract from {url}", 'on_red'))

            html_data = BeautifulSoup(r.text, "html.parser")
            links = html_data.find_all("a")

            if not links:
                return
            
            for link in links:
                href = link.get("href")
                if href:
                    parsed = urlparse(urljoin(url, href))

                    if parsed.netloc != base_domain:
                        continue

                    if parsed.scheme in {"http", "https"}:

                        cleaned_url = parsed.scheme + "://" + parsed.netloc + parsed.path

                        if cleaned_url in self.left_links:
                            continue

                        self.left_links.append(cleaned_url)

            self.scrapped_emails.update(self.ext_emails(r.text))

        except requests.RequestException as e:
            print("\r\033[K", end="", flush=True)
            print(f"\n[!] {e}")
            return
        
        except KeyboardInterrupt:
            self.print_emails(found_email=self.scrapped_emails)
            sys.exit(0)

    def run(self, args):

        # Test site: https://n1xa-cli.github.io/website-mail/
        try:
            print(self.intro())

            domain = args.get("domain")
            limit = args.get("limit")
            file = args.get("filename")
            threads = args.get("threads")

            base_domain = urlparse(domain).netloc

            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
            })

            self.left_links.append(domain)

            t = threading.Thread()

            start_time = time.perf_counter()

            while self.left_links and len(self.visited_site) < limit:
                batch = []
                
                for _ in range(threads):
                    if not self.left_links or len(self.visited_site) >= limit:
                        break

                    if not self.left_links:
                        break

                    current_link = self.left_links.popleft()

                    if self.is_visited(current_link):
                        continue

                    self.visited_site.add(current_link)

                    t = threading.Thread(target=self.scrap, args=(session, base_domain, current_link))
                    t.start()
                    batch.append(t)

                for t in batch:
                    t.join()
            
            print(colored(f"\n[+] Scrapped {len(self.visited_site)} site", 'green'))
            
            
            if file:
                self.write_to(file, self.scrapped_emails)

            end_time = time.perf_counter()
            print(colored(f"[+] Took {end_time - start_time:.3f} seconds", 'green'))

            self.print_emails(found_email=self.scrapped_emails)

        except KeyboardInterrupt:
            print(colored("\n[+] Detected Ctrl + C... Stopping...", 'red'))

        
        
        


if __name__ == "__main__":
    praser = argparse.ArgumentParser(description="An Email Scrapper.", )
    praser.add_argument("-d", "--domain", type=str, required=True, metavar="", help="Specify the domain to scrap.")
    praser.add_argument("-l", "--limit", type=int, required=False, default=20, metavar="", help="Specify the urls to scrap from(default is 20).")
    praser.add_argument("-w", "--write", type=str, required=False, default=None, metavar="", help="Write the emails to.")
    praser.add_argument("-t", "--thread", type=int,required=False, default=5, metavar="", help="Specify threads(default: 5).")
    args = praser.parse_args()

    if not args:
        praser.print_help()

    arguments = {
        "domain": args.domain,
        "limit": args.limit,
        "filename": args.write,
        "threads": args.thread
    }
        
    scrapper = EmailScrapper()
    scrapper.run(arguments)

    