import sys
import fitz  # PyMuPDF
import requests
import concurrent.futures


def check_single_url(url, headers):
    """Worker function that processes a single URL on its own thread."""
    if not url.startswith(('http://', 'https://')):
        return f"[ SKIP ] {url} (Not an HTTP/HTTPS web link)"

    try:
        # We use HEAD first because it's much faster
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)

        # Fallback to GET if HEAD is blocked
        if response.status_code >= 400:
            response = requests.get(url, headers=headers, stream=True, timeout=5)

        # Evaluate the status code
        if response.status_code < 400:
            return f"[ ALIVE ] {url}"
        elif response.status_code == 403:
            return f"[ NO ACCESS] {url} (HTTP {response.status_code})"
        else:
            return f"[ BROKEN] {url} (HTTP {response.status_code})"

    except requests.exceptions.Timeout:
        return f"[ TIMEOUT ] {url}"
    except requests.exceptions.ConnectionError:
        return f"[ BROKEN] {url} (Connection Failed / Dead Domain)"
    except requests.exceptions.RequestException as e:
        return f"[ ERROR ] {url} ({type(e).__name__})"


def verify_pdf_links(pdf_path):
    print(f"Opening {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    unique_urls = set()

    for page in doc:
        links = page.get_links()
        for link in links:
            if 'uri' in link:
                unique_urls.add(link['uri'])

    if not unique_urls:
        print("No URLs found in the PDF.")
        return

    print(f"Found {len(unique_urls)} unique links. Verifying with multi-threading...\n")
    print("-" * 50)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Use ThreadPoolExecutor to check multiple links at the same time.
    # 15 workers is a good sweet spot to go fast without triggering DDoS protections on servers.
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all URLs to the executor
        future_to_url = {executor.submit(check_single_url, url, headers): url for url in unique_urls}

        # as_completed yields the results the exact second a thread finishes,
        # meaning the terminal updates constantly rather than waiting for all 260 to finish.
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                # Retrieve the return string from our worker function and print it
                result = future.result()
                print(result)
            except Exception as exc:
                url = future_to_url[future]
                print(f"[ ERROR ] {url} generated an exception: {exc}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python PDF_link_checker.py <PDF file>")
        sys.exit(1)

    MY_PDF_FILE = sys.argv[1]
    verify_pdf_links(MY_PDF_FILE)