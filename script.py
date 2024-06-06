import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import validators
import logging
import time
import argparse
import html

def is_valid_url(url: str) -> bool:
    return validators.url(url) and url.startswith(('http://', 'https://'))

def find_broken_links(base_url: str, url: str, delay: float) -> list:
    broken_links = []
    try:
        response = requests.get(url, timeout=10, verify=True)  # Enable SSL certificate verification
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            logging.warning(f"Forbidden access to {url}: {str(e)}")
        else:
            logging.error(f"Failed to fetch the URL: {url}, Error: {str(e)}")
        return [(url, str(e))]

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [urljoin(base_url, link.get('href')) for link in soup.find_all('a', href=True)]
    images = [urljoin(base_url, img.get('src')) for img in soup.find_all('img', src=True)]

    for link in links:
        try:
            time.sleep(delay)  # Rate limit between requests
            res = requests.head(link, allow_redirects=True, timeout=5)
            if res.status_code >= 400:
                broken_links.append((link, res.status_code))
                logging.warning(f"Broken link found: {link} with status code {res.status_code}")
        except requests.RequestException as e:
            broken_links.append((link, str(e)))
            logging.error(f"Error checking link: {link} with error {str(e)}")

    missing_images = [img for img in images if requests.head(img).status_code >= 400]
    if missing_images:
        logging.warning("Missing images found:")
        for img in missing_images:
            broken_links.append((img, "Missing image"))

    return broken_links

def main():
    parser = argparse.ArgumentParser(description="Scan a website for broken links and missing images.")
    parser.add_argument("base_url", help="Base URL of the website to scan")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (in seconds)")
    args = parser.parse_args()

    logging.basicConfig(filename='web_scanner.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

    base_url = args.base_url.strip()
    if not is_valid_url(base_url):
        logging.error("Invalid base URL provided.")
        print("Invalid base URL")
        return

    broken_links = find_broken_links(base_url, base_url, args.delay)
    if not broken_links:
        logging.info("No broken links or missing images found.")
        print("No broken links or missing images found.")
    else:
        logging.info(f"{len(broken_links)} issues found.")
        print("Issues found:")
        for link, status in broken_links:
            print(f"{html.escape(link)}: {status}")

if __name__ == "__main__":
    main()
