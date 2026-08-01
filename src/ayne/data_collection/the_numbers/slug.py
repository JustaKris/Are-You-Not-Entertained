"""Pure helpers for building The Numbers movie page URL slugs.

Kept separate from `client.py` (which does the actual HTTP/parsing) so these
can be unit tested without any network access.
"""

import re
import unicodedata

BASE_URL = "https://www.the-numbers.com"

# The Numbers moves a leading article to the end of the title,
# e.g. "The Godfather" -> "Godfather, The" -> slug "Godfather-The"
_LEADING_ARTICLES = ("The", "A", "An")


def slugify(title: str) -> str:
    """Convert a movie title into a the-numbers.com URL slug.

    - Moves a leading "The"/"A"/"An" to the end (their site convention)
    - Normalizes Unicode to ASCII
    - Removes punctuation
    - Replaces whitespace with hyphens
    """
    words = title.strip().split(" ", 1)
    if len(words) == 2 and words[0] in _LEADING_ARTICLES:
        title = f"{words[1]} {words[0]}"

    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"\s+", "-", title.strip())
    return title


def candidate_urls(title: str, release_year: int | None) -> list[str]:
    """Build a short, bounded list of movie page URLs to try, in priority order.

    The Numbers frequently omits the year entirely for unambiguous titles, and
    its own internal release year occasionally differs from TMDB's by a year,
    so candidates are: no year, then the given year, then +/-1 year around it.
    """
    slug = slugify(title)
    urls = [f"{BASE_URL}/movie/{slug}"]

    if release_year:
        for year in (release_year, release_year - 1, release_year + 1):
            urls.append(f"{BASE_URL}/movie/{slug}-({year})")

    return urls
