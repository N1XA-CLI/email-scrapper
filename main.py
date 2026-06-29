#!/usr/bin/env python3

import argparse
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import sys


def get_args():
    praser = argparse.ArgumentParser(description="An Email Scrapper", )
    praser.add_argument("-d", "--domain", type=str, required=True, help="Specify the domain to scrap.")
    praser.add_argument("-l", "--limit", type=int, required=False, default=20, help="Specify the urls to scrap from(default is 20).")
    args = praser.parse_args()

    if not args:
        praser.print_help()

    return args.domain, args.limit

def is_visited(url, visited_links) -> bool:
    """Returns True if url is already visited else returns False."""
    return url in visited_links

def parse_email(found_email):

    if not found_email:
        print("[-] No Email Found")
        print("[-] Exiting...")
        sys.exit(0)
    
    print("\n[+] Found Email")
    for email in found_email:
        print(email)

def scrap(session, base_domain, email_coll, links_coll, url) -> None:

    try:
        print(f"\r\033[K[+] Scrapping from: {url}", flush=True, end="")

        r = session.get(url=url, timeout=5)

        if r.headers['Content-Type'] != "text/html":
            return
        
        r.raise_for_status()

        html_data = BeautifulSoup(r.text, "html.parser")

        links = html_data.find_all("a")

        if not links:
            print(f"[!] Cannot get link from {url}")
            return

        # Extract all the links from the page
        for link in links:
            href = link.get("href")
            if href:
                parsed = urlparse(urljoin(url, href))

                # Checks if the domain is same or not!
                if parsed.netloc != base_domain:
                    continue

                if parsed.scheme in {"http", "https"}:
                    file = parsed.path.split(".")[-1].lower()
                    cleaned_url = parsed.scheme + "://" + parsed.netloc + parsed.path
                    if cleaned_url in links_coll:
                        continue
                    links_coll.append(cleaned_url)

        # Extract all the Email from the page
        raw_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", r.text)
        email_coll.update(raw_emails)

    except requests.RequestException as e:
        print("\r\033[k", end="", flush=True)
        print(f"\n[!] {e}")
        return
    
    except KeyboardInterrupt:
        parse_email(found_email=email_coll)
        sys.exit(0)

def run():

    domain, limit = get_args() # Gets the argument

    base_domain = urlparse(domain).netloc
    
    scrapped_emails = set()
    scrapped_links = deque()
    visited_site = deque()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    scrap(domain)
    visited_site.append(domain)

    while scrapped_links and len(visited_site) < limit:
        current_link = scrapped_links.pop()

        if is_visited(current_link):
            continue

        visited_site.append(current_link)
        scrap(session, base_domain, scrapped_emails, scrapped_links, current_link)

    print(f"\n[+] Scrapped {len(visited_site)} site")
    parse_email(found_email=scrapped_emails)

if __name__ == "__main__":
    run()
