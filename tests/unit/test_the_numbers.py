"""Unit tests for The Numbers client, slug helpers, and HTML extraction."""

import asyncio

import httpx
from bs4 import BeautifulSoup

from ayne.data_collection.the_numbers.client import (
    TheNumbersClient,
    extract_financial_data,
    parse_money,
)
from ayne.data_collection.the_numbers.slug import candidate_urls, slugify


class TestSlugify:
    def test_simple_title(self):
        assert slugify("Toy Story 4") == "Toy-Story-4"

    def test_leading_the_moved_to_end(self):
        assert slugify("The Godfather") == "Godfather-The"

    def test_leading_a_moved_to_end(self):
        assert slugify("A Quiet Place") == "Quiet-Place-A"

    def test_leading_an_moved_to_end(self):
        assert slugify("An Education") == "Education-An"

    def test_punctuation_is_stripped(self):
        assert slugify("Avengers: Infinity War") == "Avengers-Infinity-War"

    def test_the_not_moved_when_not_first_word(self):
        # "The" only gets moved when it's the leading word of the title.
        assert slugify("Not The Godfather") == "Not-The-Godfather"


class TestCandidateUrls:
    def test_no_year_gives_single_no_year_candidate(self):
        urls = candidate_urls("Toy Story 4", None)
        assert urls == ["https://www.the-numbers.com/movie/Toy-Story-4"]

    def test_year_adds_year_and_offby_one_candidates(self):
        urls = candidate_urls("Toy Story 4", 2019)
        assert urls[0] == "https://www.the-numbers.com/movie/Toy-Story-4"
        assert "https://www.the-numbers.com/movie/Toy-Story-4-(2019)" in urls
        assert "https://www.the-numbers.com/movie/Toy-Story-4-(2018)" in urls
        assert "https://www.the-numbers.com/movie/Toy-Story-4-(2020)" in urls
        assert len(urls) == 4


class TestParseMoney:
    def test_simple_amount(self):
        assert parse_money("$1,071,177,215") == 1071177215

    def test_amount_with_trailing_commentary(self):
        assert (
            parse_money("$200,000,000 (worldwide box office is 5.4 times production budget)")
            == 200000000
        )

    def test_no_amount_returns_none(self):
        assert parse_money("N/A") is None


class TestExtractFinancialData:
    def test_extracts_plain_space_labels(self):
        html = """
        <table id="movie_finances">
            <tr><td><b>Domestic Box Office</b></td><td class="data">$434,038,008</td></tr>
            <tr><td><b>International Box Office</b></td><td class="data">$637,139,207</td></tr>
            <tr><td><b>Worldwide Box Office</b></td><td class="data">$1,071,177,215</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        data = extract_financial_data(soup)
        assert data == {
            "domestic_box_office": 434038008,
            "international_box_office": 637139207,
            "worldwide_box_office": 1071177215,
        }

    def test_extracts_labels_with_nonbreaking_space(self):
        # The real site uses \xa0 (non-breaking space) between words in some
        # labels instead of a regular space - this must still match.
        html = (
            "<table>"
            "<tr><td><b>Opening\xa0Weekend:</b></td>"
            "<td>$120,908,065 (27.9% of total gross)</td></tr>"
            "<tr><td><b>Production\xa0Budget:</b></td>"
            "<td>$200,000,000 (worldwide box office is 5.4 times production budget)</td></tr>"
            "</table>"
        )
        soup = BeautifulSoup(html, "html.parser")
        data = extract_financial_data(soup)
        assert data == {
            "opening_weekend_box_office": 120908065,
            "production_budget": 200000000,
        }

    def test_unknown_labels_are_ignored(self):
        html = """
        <table>
            <tr><td><b>Some Unrelated Field:</b></td><td>$999</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert extract_financial_data(soup) == {}


class TestTheNumbersClient:
    def test_request_count_tracks_candidate_attempts_and_resets_per_batch(self):
        async def run_test() -> tuple[int, int, int]:
            def handler(request: httpx.Request) -> httpx.Response:
                return httpx.Response(status_code=404, request=request)

            client = TheNumbersClient(requests_per_second=1_000)
            client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            movie = {"movie_id": 1, "title": "Missing Film", "release_year": 2024}
            try:
                await client.get_batch_financial_data([movie])
                first_count = client.last_request_count
                await client.get_batch_financial_data([movie])
                second_count = client.last_request_count
                return first_count, second_count, len(candidate_urls(movie["title"], 2024))
            finally:
                await client.close()

        first_count, second_count, expected_count = asyncio.run(run_test())

        assert first_count == expected_count
        assert second_count == expected_count

    def test_rows_with_fewer_than_two_cells_are_skipped(self):
        html = "<table><tr><td>Domestic Box Office</td></tr></table>"
        soup = BeautifulSoup(html, "html.parser")
        assert extract_financial_data(soup) == {}
