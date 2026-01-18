#by copilot
import os
import time
from typing import Optional, Tuple
import requests

BROWSER_HEADERS = {
    # A realistic modern UA (update as needed)
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}
def save_openalex_pdf(openalex_loc: str,doi: str, out_dir: str) -> str:
    """
    Returns a status string: 'saved', 'forbidden', 'not_oa', 'no_link', 'failed'
    """
    # Only proceed if OA
    
    pdf_url = openalex_loc
    
    target_url = pdf_url

    # Build deterministic filename
    filename = f"{doi.replace('/', '_')}.pdf"
    out_path = os.path.join(out_dir, filename)

    ok, code, err = download_pdf_with_session(
        pdf_url=target_url,
        out_path=out_path,
        referer= None,
        warmup_url=None,
    )
    
    if ok:
        return "saved"
    if code in (403, 429):
        return "forbidden"
    return "failed"

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def looks_like_pdf(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "").lower()
    # Some hosts return octet-stream; content sniffing would be slower, so we allow both
    return ("application/pdf" in ctype) or ("application/octet-stream" in ctype)

def download_pdf_with_session(
    pdf_url: str,
    out_path: str,
    referer: Optional[str] = None,
    warmup_url: Optional[str] = None,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
    timeout: int = 30,
) -> Tuple[bool, int, Optional[str]]:
    """
    Attempts to download a PDF to out_path.
    Returns (success, status_code, error_message_or_None).
    """
    
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)

    # Optionally warm up by visiting landing page to set cookies
    if warmup_url:
        try:
            session.get(warmup_url, timeout=timeout, allow_redirects=True)
            time.sleep(0.3)  # be polite
        except requests.RequestException as e:
            # Warmup may fail on some hosts; we can still attempt direct PDF
            pass

    # Add per-request headers like Referer
    req_headers = {}
    if referer:
        req_headers["Referer"] = referer

    last_status = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(
                pdf_url,
                headers=req_headers,
                timeout=timeout,
                allow_redirects=True,
                stream=True,  # stream large files safely
            )
            last_status = resp.status_code

            # Respect rate limits / forbidden
            if resp.status_code in (403, 429):
                # Backoff and retry a couple of times
                time.sleep(backoff_seconds * attempt)
                continue

            if not resp.ok:
                # e.g., 404, 410, 500, etc.
                return False, resp.status_code, f"HTTP {resp.status_code}"

            # Verify content type looks like PDF, some hosts mislabel; we allow octet-stream
            if not looks_like_pdf(resp):
                # It might still be a PDF; you could sniff the first bytes "%PDF", but that means reading content.
                # Here we fail fast to avoid saving HTML.
                return False, resp.status_code, f"Unexpected content type: {resp.headers.get('Content-Type')}"

            # Write to disk
            ensure_dir(os.path.dirname(out_path))
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)

            return True, resp.status_code, None

        except requests.RequestException as e:
            # network error
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
                continue
            return False, last_status or 0, str(e)

    # If we exhausted retries due to 403/429
    return False, last_status or 0, f"Failed after {max_retries} attempts"
