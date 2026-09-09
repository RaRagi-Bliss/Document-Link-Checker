import sys
import fitz  # PyMuPDF
import requests


def verify_pdf_links(pdf_path):
    print(f"Opening {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    # Using a set to avoid checking duplicate links multiple times
    unique_urls = set()

    # Step 1: Extract all links from every page
    for page in doc:
        links = page.get_links()
        for link in links:
            # Check if the link is a standard URL (URI)
            if 'uri' in link:
                unique_urls.add(link['uri'])

    if not unique_urls:
        print("No URLs found in the PDF.")
        return

    print(f"Found {len(unique_urls)} unique links. Verifying...\n")
    print("-" * 50)

    # Step 2: Test each link
    headers = {
        # Using a standard browser User-Agent because some websites block basic Python bots
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for url in unique_urls:
        if not url.startswith(('http://', 'https://')):
            print(f"[SKIP] {url} (Not an HTTP/HTTPS web link)")
            continue

        try:
            # We use HEAD first because it's much faster than downloading the whole page
            response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)

            # Some servers block HEAD requests (returning 400+ errors).
            # If that happens, we fall back to a standard GET request.
            if response.status_code >= 400:
                response = requests.get(url, headers=headers, stream=True, timeout=5)

            if response.status_code < 400:
                print(f"[ ALIVE ] {url}")
            else:
                if response.status_code == 403:
                    print(f"[ NO ACCESS] {url} (HTTP {response.status_code})")
                else:    
                    print(f"[ BROKEN] {url} (HTTP {response.status_code})")

        except requests.exceptions.Timeout:
            print(f"[ TIMEOUT ] {url}")
        except requests.exceptions.RequestException as e:
            print(f"[ ERROR ] {url} ({type(e).__name__})")


if __name__ == "__main__":
    # Replace with the path to your PDF
    if len(sys.argv) < 2:
        print("Usage: python PDF_link_checker.py <PDF file>")
    MY_PDF_FILE = sys.argv[1]
    verify_pdf_links(MY_PDF_FILE)