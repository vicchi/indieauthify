"""
IndieAuthify: common package; URL utilities module
"""


def normalise_url(url: str, noslash=True, noscheme=True) -> str:
    """
    Normalise a URL optionally removing a trailing slash and/or the HTTP scheme
    """

    if noslash:
        url = url.strip('/')

    if noscheme:
        url = url.replace('https://', '').replace('http://', '')

    return url
