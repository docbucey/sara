"""CORE Network: HTTP client, HTML parsing, BuceyShunt HTTP class."""
import json
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import urllib.request
import urllib.parse


class BuceyShunt:
    def __init__(self, device_id, offset, control_byte):
        # 8-bit fields
        self.device_id = device_id & 0xFF
        self.offset = offset & 0xFF
        self.control = control_byte & 0xFF

    @property
    def state(self):
        # top 2 bits (2-4-2)
        return (self.control >> 6) & 0b11

    @property
    def agency_type(self):
        # middle 4 bits (2-4-2)
        return (self.control >> 2) & 0b1111

    @property
    def exec_mode(self):
        # bottom 2 bits (2-4-2)
        return self.control & 0b11

    def encode(self):
        # This is the raw 8-8-8 binary header
        return bytes([self.device_id, self.offset, self.control])


# ---------------------------------------------------------
# Metadata structure (UTF-8/2)
# ---------------------------------------------------------
def make_metadata(url, content_type):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    return {
        "domain": domain,
        "content_type": content_type.split(";")[0].strip().lower()
    }


# ---------------------------------------------------------
# HTML -> Text extractor (offset 0x10)
# ---------------------------------------------------------
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data.strip())

    def get_text(self):
        return " ".join(self.text_parts)


def extract_text(html_bytes, url, content_type):
    try:
        html = html_bytes.decode("utf-8", errors="ignore")
    except:
        html = ""

    parser = TextExtractor()
    parser.feed(html)
    text = parser.get_text()

    metadata = make_metadata(url, content_type)
    return text, metadata


# ---------------------------------------------------------
# HTML -> Links extractor (offset 0x11)
# ---------------------------------------------------------
class LinkExtractor(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.links = []
        self.base_url = base_url

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for (attr, value) in attrs:
                if attr.lower() == "href" and value:
                    full = urllib.parse.urljoin(self.base_url, value)
                    self.links.append(full)

    def get_links(self):
        return self.links

def extract_links(html_bytes, url, content_type):
    try:
        html = html_bytes.decode("utf-8", errors="ignore")
    except:
        html = ""

    parser = LinkExtractor(url)
    parser.feed(html)
    links = parser.get_links()

    metadata = make_metadata(url, content_type)
    return links, metadata


# ---------------------------------------------------------
# HTTP GET (device 0x20)
# ---------------------------------------------------------
def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SARA-Gen0A"})
    with urllib.request.urlopen(req) as response:
        content_type = response.headers.get("Content-Type", "text/html")
        data = response.read()
        return data, content_type
