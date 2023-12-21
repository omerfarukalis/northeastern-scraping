from __future__ import annotations
from typing import Any, Final, Literal, Optional, Union

import datetime
import math
import re

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.models import Response

INVALID_INPUT: Final = 400
INVALID_API_KEY: Final = 401
NO_ACCESS: Final = 403
DOES_NOT_EXIST: Final = 404

# Define all URLs that are needed
BASE_URL: Final = "api.nytimes.com/svc/"
BASE_TOP_STORIES: Final = BASE_URL + "topstories/v2/"
BASE_MOST_POPULAR: Final = BASE_URL + "mostpopular/v2/"
BASE_META_DATA: Final = BASE_URL + "news/v3/content.json"
BASE_TAGS: Final = BASE_URL + "semantic/v2/concept/suggest"
BASE_ARCHIVE_METADATA: Final = BASE_URL + "archive/v1/"
BASE_ARTICLE_SEARCH: Final = BASE_URL + "search/v2/articlesearch.json"
BASE_LATEST_ARTICLES: Final = BASE_URL + "news/v3/content/"
BASE_SECTION_LIST: Final = BASE_URL + "news/v3/content/section-list.json"
TIMEOUT: Final = (10, 30)

def article_metadata_set_url(url: str) -> dict[str, str]:
    # Raise error if url is not an str
    if not isinstance(url, str):
        raise TypeError("URL needs to be str")
    # Set metadata in requests params and define URL
    options = {"url": url}

    return options


def article_metadata_check_valid(result: list[dict[str, Any]]):
    # Check if result is valid
    if result[0].get("published_date") == "0000-12-31T19:03:58-04:56":
        raise ValueError(
            "Invalid URL, the API cannot parse metadata from live articles"
        )

NoneType: Final = type(None)


def _article_search_result_warnings(results: int):
    # Show warnings when a lot of results are requested
    if results >= 100:
        warnings.warn(
            "Asking for a lot of results, because of rate"
            + " limits it can take a while."
        )

    # Show waring when above maximum amount of results
    if results >= 2010:
        warnings.warn(
            "Asking for more results then the API can provide,"
            + "loading maximum results."
        )


def _article_search_check_type(
    query: Optional[str],
    dates: dict[str, Union[datetime.date, datetime.datetime, None]],
    options: dict[str, Any],
    results: int,
):
    # Check if types are correct
    if not isinstance(query, (str, NoneType)):
        raise TypeError("Query needs to be None or str")

    if not isinstance(dates, dict):
        raise TypeError("Dates needs to be a dict")

    if not isinstance(options, dict):
        raise TypeError("Options needs to be a dict")

    if not isinstance(results, (int, NoneType)):
        raise TypeError("Results needs to be None or int")


def _article_search_check_sort_options(options: dict[str, str]):
    # Get and check if sort option is valid
    sort = options.get("sort")

    if sort not in [None, "newest", "oldest", "relevance"]:
        raise ValueError("Sort option is not valid")


def _article_search_check_date_types(dates: dict[str, Any]):
    # Raise error if date is incorrect type
    date_types = (datetime.datetime, datetime.date, NoneType)

    begin_date = dates.get("begin_date")
    if not isinstance(begin_date, date_types):
        raise TypeError(
            "Begin date needs to be datetime.datetime, datetime.date or None"
        )

    end_date = dates.get("end_date")
    if not isinstance(end_date, date_types):
        raise TypeError(
            "End date needs to be datetime.datetime, datetime.date or None"
        )


def article_search_check_input(
    query: Optional[str],
    dates: dict[str, Union[datetime.date, datetime.datetime, None]],
    options: dict[str, Any],
    results: int,
) -> None:
    """Check input of article_search"""
    _article_search_check_type(query, dates, options, results)
    _article_search_check_sort_options(options)
    _article_search_check_date_types(dates)
    _article_search_result_warnings(results)


def _convert_date_to_str(
    date: Union[datetime.datetime, datetime.date, None]
) -> Optional[str]:
    if date is not None:
        return datetime.datetime(date.year, date.month, date.day).strftime(
            "%Y%m%d"
        )

    return None


def article_search_parse_dates(
    dates: dict[str, Union[datetime.datetime, datetime.date, None]]
) -> tuple[Optional[str], Optional[str]]:
    """Parse dates into options"""
    # Get dates if defined
    begin_date = dates.get("begin")
    end_date = dates.get("end")
    return (_convert_date_to_str(begin_date), _convert_date_to_str(end_date))


def _filter_input(values: list) -> str:
    input = ""
    # Add all the data in the list to the filter
    for i, value in enumerate(values):
        input += f'"{value}"'
        if i < len(values) - 1:
            input += " "

    return input


def article_search_parse_options(options: dict[str, Any]) -> dict:
    """Help to create all fq queries"""
    # pylint: disable=invalid-name
    # Get options already defined in fq (filter query)
    fq = options.get("fq", "")

    # Set query options that are currently supported
    current_filter_support = [
        "source",
        "news_desk",
        "section_name",
        "glocation",
        "type_of_material",
    ]

    # Run for every filter
    for _filter in current_filter_support:
        # Get data for filter if it's not defined continue to next filter
        values = options.get(_filter)
        if values is None:
            continue

        # Check if filter query is already defined. If it is then add
        # " AND " to the query
        if len(fq) != 0:
            fq += " AND "

        # Add filter
        filter_input = _filter_input(values)
        fq += f"{_filter}:({filter_input})"

        # Remove the filter from options
        options.pop(_filter)

    # Set fq in options
    options["fq"] = fq

    # Return the options
    return options

def parse_date(
    date_string: str,
    date_type: Literal["rfc3339", "date-only", "date-time"],
) -> Union[datetime.datetime, datetime.date, None]:
    """Parse the date into datetime.datetime object"""
    # If date_string is None return None
    if date_string is None:
        return None

    date: Union[datetime.datetime, datetime.date]

    # FIXME this should probabily be split up
    if date_type == "rfc3339":
        date = datetime.datetime.strptime(
            date_string,
            "%Y-%m-%dT%H:%M:%S%z",
        )
    elif date_type == "date-only":
        if re.match(r"^(\d){4}-00-00$", date_string):
            date = datetime.datetime.strptime(date_string, "%Y-00-00").date()

        date = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
    elif date_type == "date-time":
        date = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

    return date


def parse_dates(
    articles: list[dict[str, str]],
    date_type: Literal["rfc3339", "date-only", "date-time"],
    locations: Optional[list] = None,
) -> list[dict[str, Any]]:
    """Parse dates to datetime"""
    # Create list locations is None
    if locations is None:
        locations = []

    # Create parsed_articles list
    parsed_articles: list[dict[str, Any]] = []

    # For every article parse date_string into datetime.datetime
    for article in articles:
        parsed_article: dict[str, Any] = article
        for location in locations:
            parsed_article[location] = parse_date(
                parsed_article[location], date_type
            )
        parsed_articles.append(article)

    return parsed_articles

def raise_for_status(res: Response):
    if res.status_code == INVALID_INPUT:
        raise ValueError("Error 400: Invalid input")

    if res.status_code == INVALID_API_KEY:
        raise ValueError("Error 401: Invalid API Key")

    if res.status_code == NO_ACCESS:
        raise RuntimeError("Error 403: You don't have access to this page")

    if res.status_code == DOES_NOT_EXIST:
        raise RuntimeError("Error 404: This page does not exist")

    res.raise_for_status()


def get_from_location(
    parsed_res: dict[str, Any],
    location: Optional[list[str]],
) -> list[dict[str, Any]]:

    if location is None:
        return parsed_res["results"]

    # Sometimes the results are in a different location,
    # this location can be defined in a list
    # Then load the data from that location
    else:
        results: Any = parsed_res
        for loc in location:
            results = results[loc]

    return results

class NytApi:
    """
    This api collects data from NewYork Times API.
    """

    key: str
    https: bool
    session: Session
    backoff: bool
    user_agent: str
    parse_dates: bool

    def __init__(
        self,
        key: str = None,
        https: bool = True,
        session: Optional[Session] = None,
        backoff: bool = True,
        user_agent: Optional[str] = None,
        parse_dates: bool = False,
    ):
        self.__set_key(key)
        self.__set_session(session)
        self.__set_parse_dates(parse_dates)
        self.__set_protocol(https)
        self.__set_backoff(backoff)
        self.__set_user_agent(user_agent)

    def __set_key(self, key: Optional[str]):
        if key is None:
            raise ValueError(
                "API key is not set, get an API-key from "
                + "https://developer.nytimes.com."
            )

        if not isinstance(key, str):
            raise TypeError("API key needs to be str")

        self.key: str = key

    def __set_session(self, session: Optional[Session]):
        self._local_session = False
        if session is None:
            self._local_session = True
            session = Session()

        if not isinstance(session, Session):
            raise TypeError("Session needs to be a Session object")

        self.session = session

    def __set_parse_dates(self, parse_dates: bool):
        if not isinstance(parse_dates, bool):
            raise TypeError("parse_dates needs to be bool")

        self.parse_dates = parse_dates

    def __set_protocol(self, https: bool):
        if not isinstance(https, bool):
            raise TypeError("https needs to be bool")

        if https:
            self.protocol = "https://"
        else:
            self.protocol = "http://"

    def __set_backoff(self, backoff: bool):
        # Set strategy to prevent HTTP 429 (Too Many Requests) errors
        if not isinstance(backoff, bool):
            raise TypeError("backoff needs to be bool")

        if backoff:
            backoff_strategy: Any = Retry(
                total=10,
                backoff_factor=1,
                status_forcelist=[429, 509],
            )

            adapter = HTTPAdapter(max_retries=backoff_strategy)

            self.session.mount(self.protocol + "api.nytimes.com/", adapter)

    def __set_user_agent(self, user_agent: Optional[str]):
        # Set header to show that this wrapper is used
        if user_agent is None:
            user_agent = "pynytimes/1.0"

        if not isinstance(user_agent, str):
            raise TypeError("user_agent needs to be str")

        self.session.headers.update({"User-Agent": user_agent})

    def __enter__(self) -> NYTAPI:
        return self

    def __load_data(
        self,
        url: str,
        options: Optional[dict[str, Any]] = None,
        location: Optional[list[str]] = None,
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """This function loads the data for the wrapper for most API use cases"""
        # Set API key in query parameters
        params = {"api-key": self.key}

        # Add options to query parameters
        params.update(options or {})  # add empty list if None

        # Load the data from the API, raise error if there's an invalid status
        # code
        res = self.session.get(
            f"{self.protocol}{url}",
            params=params,
            timeout=TIMEOUT,
        )

        raise_for_status(res)
        parsed_res: dict[str, Any] = res.json()
        return get_from_location(parsed_res, location)

    def __parse_dates(
        self,
        articles: list[dict[str, str]],
        date_type: Literal["rfc3339", "date-only", "date-time"],
        locations: Optional[list] = None,
    ) -> list[dict[str, Any]]:
        """Parse dates to datetime"""
        # Don't parse if parse_dates is False
        return (
            parse_dates(articles, date_type, locations)
            if self.parse_dates
            else articles
        )

    def article_metadata(self, url: str) -> list[dict[str, Any]]:
        """Load metadata of an article by url

        Args:
            url (str): URL of an New York Times article

        Returns:
            list[dict[str, Any]]: List of article metadata
        """
        options = article_metadata_set_url(url)

        # Load, parse and return the data
        result: list[dict[str, Any]] = self.__load_data(
            url=BASE_META_DATA, options=options
        )  # type:ignore

        article_metadata_check_valid(result)

        date_locations = [
            "updated_date",
            "created_date",
            "published_date",
            "first_published_date",
        ]
        parsed_result = self.__parse_dates(result, "rfc3339", date_locations)
        return parsed_result

    def section_list(self) -> list[dict[str, Any]]:
        """Load all list of all sections

        Returns:
            list[dict[str, Any]]: List of sections
        """
        # Set URL, load and return the data
        return self.__load_data(url=BASE_SECTION_LIST)  # type:ignore

    def latest_articles(
        self,
        source: Literal["all", "nyt", "inyt"] = "all",
        section: str = "all",
    ) -> list[dict[str, Any]]:
        """Load latest articles

        Args:
            source (Literal["all", "nyt", "inyt"], optional): Select sources to get all
            articles from. Defaults to "all".
            section (str, optional): Section to get all latest articles from.
            Defaults to "all".

        Raises:
            ValueError: Section is not a valid option

        Returns:
            list[dict[str, Any]]: List of metadata of latest articles
        """
        latest_articles_check_types(source, section)

        # Set URL, load and return data
        url = f"{BASE_LATEST_ARTICLES}{source}/{section}.json"
        try:
            result: list[dict[str, Any]] = self.__load_data(url)  # type:ignore
        except RuntimeError:
            raise ValueError("Section is not a valid option")

        date_locations = [
            "updated_date",
            "created_date",
            "published_date",
            "first_published_date",
        ]
        parsed_result = self.__parse_dates(result, "rfc3339", date_locations)
        return parsed_result

    def tag_query(
        self,
        query: str,
        filter_option: Optional[dict[str, Any]] = None,
        filter_options: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[str]:
        """Load Times Tags

        Args:
            query (str): Search query to find a tag
            filter_option (Optional[dict[str, Any]], optional): Filter the tags.
            Defaults to None.
            filter_options (Optional[str], optional): Filter options. Defaults
            to None.
            max_results (Optional[int], optional): Maximum number of results.
            None means no limit. Defaults to None.

        Returns:
            list[str]: List of tags
        """
        # Raise error for TypeError
        tag_query_check_types(query, max_results)

        _filter_options = (
            tag_query_get_filter_options(filter_options) or filter_option
        )

        # Add options to request params
        options = {"query": query, "filter": _filter_options}

        # Define amount of results wanted
        if max_results is not None:
            options["max"] = str(max_results)

        # Set URL, load and return data
        return self.__load_data(url=BASE_TAGS, options=options, location=[])[
            1
        ]  # type:ignore

    def archive_metadata(
        self, date: Union[datetime.datetime, datetime.date]
    ) -> list[dict[str, Any]]:
        """Load all article metadata from the last month

        Args:
            date (Union[datetime.datetime, datetime.date]): The month of
            which you want to load all article metadata from

        Raises:
            TypeError: Date is not a datetime or date object

        Returns:
            list[dict[str, Any]]: List of article metadata
        """
        # Raise Error if date is not defined
        if not isinstance(date, (datetime.datetime, datetime.date)):
            raise TypeError("Date has to be datetime or date")

        # Set URL, load and return data
        url = f"{BASE_ARCHIVE_METADATA}{date.year}/{date.month}.json"

        parsed_result = self.__parse_dates(
            self.__load_data(  # type:ignore
                url, location=["response", "docs"]
            ),
            "rfc3339",
            ["pub_date"],
        )
        return parsed_result

    def __article_search_load_data(
        self,
        results: int,
        options: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result = []
        for i in range(math.ceil(results / 10)):
            # Set page
            options["page"] = str(i)

            location = ["response"]
            # Load data and raise error if there's and error status
            res: dict[str, Any] = self.__load_data(  # type:ignore
                url=BASE_ARTICLE_SEARCH, options=options, location=location
            )

            # Parse results and append them to results list
            result += res.get("docs")  # type:ignore

            # Stop loading if all responses are already loaded
            if res.get("meta", {}).get("hits", 0) <= i * 10:
                break

        return result

    def article_search(
        self,
        query: Optional[str] = None,
        dates: Optional[
            dict[str, Union[datetime.date, datetime.datetime, None]]
        ] = None,
        options: Optional[dict[str, Any]] = None,
        results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search New York Times articles

        Args:
            query (Optional[str], optional): Search query. Defaults to None.
            dates (Optional[ dict[str, Union[datetime.date, datetime.datetime, None]]
            ], optional):
            Values between which results should be. Defaults to None.
            options (Optional[dict[str, Any]], optional): Options for the
            search results.
            Defaults to None.
            results (int, optional): Load at most this many articles. Defaults to 10.

        Returns:
            list[dict[str, Any]]: Article metadata
        """
        # Set if None
        dates = dates or {}
        options = options or {}

        # Check if input is valid
        article_search_check_input(query, dates, options, results)

        # Limit results loading to 2010
        results = min(results, 2010)

        # Resolve filter options into fq
        options = article_search_parse_options(options)

        # Parse dates into options
        # FIXME I really don't get this error
        begin_date, end_date = article_search_parse_dates(dates)
        options["begin_date"] = begin_date
        options["end_date"] = end_date

        # Set query if defined
        if query is not None:
            options["q"] = query

        # Set result list and add request as much data as needed
        result = self.__article_search_load_data(results, options)

        # Parse and return results
        parsed_result = self.__parse_dates(result, "rfc3339", ["pub_date"])
        return parsed_result

    # Allow the option to close the session
    def close(self) -> None:
        """Close session"""
        # Close session only if it exists
        if hasattr(self, "session"):
            self.session.close()

    # Close session before delete
    def __del__(self) -> None:
        """Close session on deletion"""
        if getattr(self, "_local_session", False) is True:
            self.close()

    def __exit__(self, *args) -> None:
        """Close session on exit"""
        if getattr(self, "_local_session", False) is True:
            self.close()


