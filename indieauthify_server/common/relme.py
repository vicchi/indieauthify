"""
IndieAuthify: common package; rel=me utilities module
"""

from http import HTTPStatus
from typing import List
import urllib.parse

from bs4 import BeautifulSoup
from indieweb_utils.parsing.parse import get_parsed_mf2_data
from indieweb_utils.utils.urls import canonicalize_url
from pydantic import HttpUrl
import requests
from indieauthify_server.common.url import normalise_url

from indieauthify_server.dependencies.settings import get_settings


def get_relme_links(url: HttpUrl, require_link_back: bool = True) -> List[str]:
    """
    Get the valid links on a page that link back to a rel=me URL
    """

    domain = urllib.parse.urlparse(url).netloc
    canonical_url = normalise_url(canonicalize_url(url, domain), noslash=True, noscheme=False)
    mf2_data = get_parsed_mf2_data(parsed_mf2=None, html=None, url=canonical_url)
    relme_links = [canonicalize_url(url, domain) for url in mf2_data['rels'].get('me', [])]
    valid_links = set()

    if not require_link_back:
        return list(set(relme_links))

    settings = get_settings()
    for link in relme_links:
        try:
            resp = requests.get(link, timeout=settings.rpc_timeout)
        except requests.exceptions.RequestException:
            continue

        if resp.status_code != HTTPStatus.OK:
            continue

        parsed_page = BeautifulSoup(resp.text, 'html.parser')
        page_links = parsed_page.find_all('a') + parsed_page.find_all('link')
        link_domain = urllib.parse.urlparse(link).netloc

        for item in page_links:
            if not item.get('rel') and require_link_back:
                continue

            if 'me' not in item.get('rel', '') and require_link_back:
                continue

            if item.get('href') == canonical_url:
                canonical_link = canonicalize_url(link, link_domain)
                valid_links.add(canonical_link)

    return list(valid_links)
