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


def is_visited(url) -> bool:
    """Returns True if url is already visited else returns False."""
    if url in visited_site:
        return True
    return False

# https://mas.bg.ac.rs/ # Site to test
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def scrap(url, scrape_links = False) -> None:

    try:
        print(f"\r\033[K[+] Scrapping from: {url}", flush=True, end="")

        r = session.get(url=url, timeout=5)
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
                    if file in exclude_filetype:
                        continue
                    if scrape_links:
                        cleaned_url = parsed.scheme + "://" + parsed.netloc + parsed.path
                        if cleaned_url in scrapped_links:
                            continue
                        scrapped_links.append(cleaned_url)

        # Extract all the Email from the page
        raw_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", r.text)
        scrapped_emails.update(raw_emails)

    except requests.RequestException as e:
        print("\r\033[k", end="", flush=True)
        print(f"\n[!] {e}")
        return
    
    except KeyboardInterrupt:
        print()
        if scrapped_emails:
            print("[+] Found Email")
            print(*scrapped_emails, sep="\n")
        else:
            print("[-] No Email Found")
        sys.exit(0)


domain, limit = get_args()

base_domain = urlparse(domain).netloc
exclude_filetype = {"pdf", "png", "jpg", "jpeg", "gif", "webp", "svg", "ico", "bmp", "mp3", "wav", "ogg", "flac", "aac", "m4a", "mp4", "mkv", "avi", "mov", "webm", "wmv", "mpeg", "mpg", "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "exe", "msi", "apk", "deb", "rpm", "dmg", "pkg", "appimage", "iso", "img", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "rtf", "csv", "ttf", "otf", "woff", "woff2", "dll", "so", "bin", "jar", "class", "pyc"}

scrapped_emails = set()
scrapped_links = deque()

visited_site = deque()

# Extract links and emails form the site.
scrap(domain, scrape_links=True)

visited_site.append(domain)

while scrapped_links and len(visited_site) < limit:
    current_link = scrapped_links.pop()

    if is_visited(current_link):
        continue

    visited_site.append(current_link)

    scrap(current_link, scrape_links=True)

print()
print(f"[+] Scrapped {len(visited_site)} site")

print(f"[+] Scrapped {len(scrapped_emails)} email")

if scrapped_emails:
    print("[+] Found Email")
    print(*scrapped_emails, sep="\n")
else:
    print("[-] No Email Found")

