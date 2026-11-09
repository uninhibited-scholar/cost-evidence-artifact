#!/usr/bin/env python3
"""Fetch a cited paper from arXiv so a reviewer can spot-check verbatim quotes.

    python3 code/fetch_source.py 2610.28425 [more ids...] [--source]

For each arXiv id this downloads, into <artifact root>/fetch/:
  * the Atom metadata (title, abstract, versions) from export.arxiv.org, and
  * the PDF of the latest version (default) or the LaTeX e-print source
    (--source), from arxiv.org.

Why: full paper texts are NOT redistributed in this artifact (arXiv licenses
differ per paper). The evidence cards record verbatim quotes together with
section/table locators and the version that was read (versions_read); this
script lets a reviewer retrieve the cited version and check a quote in place.

Notes
  * Network access happens ONLY when you run this script; nothing else in the
    artifact touches the network.
  * Verbatim matching against the PDF-extracted text of a different arXiv
    version can fail on line breaks and math tokens; the cards record which
    version was read (versions_read), so prefer that version when checking.
  * Be polite to arXiv: the script sleeps 3 seconds between requests.
"""
import argparse
import ipaddress
import socket
import sys
import time
from pathlib import Path
from urllib import request as urlreq
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fetch"

# --- egress guard: static allowlist + resolved-IP check (no redirects followed) --
ALLOWED_HOSTS = {"export.arxiv.org", "arxiv.org"}
MAX_BYTES = 64 * 1024 * 1024


def guard_url(url):
    u = urlparse(url)
    if u.scheme != "https":
        raise ValueError(f"only https is allowed, got {u.scheme}")
    if u.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"host {u.hostname!r} is not in the allowlist {sorted(ALLOWED_HOSTS)}")
    for fam, typ, _, _, sockaddr in socket.getaddrinfo(u.hostname, 443):
        ip = ipaddress.ip_address(sockaddr[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise ValueError(f"{u.hostname} resolves to a non-public address ({ip}); blocking")
    return url


def get(url, dest, binary=True):
    guard_url(url)
    # no redirects are followed automatically for cross-host hops; opener is default
    req = urlreq.Request(url, headers={"User-Agent": "artifact-quote-checker/1.0"})
    with urlreq.urlopen(req, timeout=60) as r:
        final = urlparse(r.geturl())
        if final.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"redirected to non-allowlisted host {final.hostname!r}; blocking")
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("response exceeds the 64 MB cap")
    dest.write_bytes(data) if binary else dest.write_text(data.decode("utf-8", "replace"))
    return dest


def parse_atom(xml_text, aid):
    # harden: refuse DTDs/entity declarations before parsing (standard library
    # ElementTree would otherwise accept internal entity expansion)
    head = xml_text[:4096].lower()
    if "<!doctype" in head or "<!entity" in head:
        raise ValueError("DTD/entity declarations are not accepted in Atom responses")
    if len(xml_text) > 4 * 1024 * 1024:
        raise ValueError("Atom response exceeds the 4 MB cap")
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    return root.find("a:entry", ns)


def fetch_one(aid, want_source):
    aid = aid.strip()
    if not __import__("re").fullmatch(r"[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?|[0-9]{7}", aid):
        raise ValueError(f"not a plain arXiv id: {aid!r}")
    xml = get(f"https://export.arxiv.org/api/query?id_list={aid}&max_results=1",
              OUT / f"{aid}.atom.xml", binary=False)
    entry = parse_atom(xml, aid)
    if entry is None:
        print(f"{aid}: NOT FOUND on arXiv (check the id)")
        return False
    title = " ".join((entry.findtext("a:title", "", {"a": "http://www.w3.org/2005/Atom"}) or "").split())
    abstract = " ".join((entry.findtext("a:summary", "", {"a": "http://www.w3.org/2005/Atom"}) or "").split())
    published = entry.findtext("a:published", "", {"a": "http://www.w3.org/2005/Atom"})
    print(f"{aid}: {title}")
    print(f"   published {published[:10]}")
    print(f"   abstract: {abstract[:180]}...")
    dest = OUT / (f"{aid}.tar.gz" if want_source else f"{aid}.pdf")
    url = f"https://arxiv.org/e-print/{aid}" if want_source else f"https://arxiv.org/pdf/{aid}"
    get(url, dest)
    print(f"   saved {dest.relative_to(ROOT)}  ({dest.stat().st_size} bytes)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--source", action="store_true",
                    help="fetch the LaTeX e-print source instead of the PDF")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ok = True
    for i, aid in enumerate(args.ids):
        if i:
            time.sleep(3)  # arXiv politeness
        try:
            ok = fetch_one(aid, args.source) and ok
        except Exception as e:
            print(f"{aid}: fetch failed ({e})")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
