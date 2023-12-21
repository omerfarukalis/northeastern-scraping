import warnings
from typing import List
import urllib.request as libreq
import urllib
import requests
import feedparser
from datetime import datetime
import itertools
import pandas as pd
from pathlib import Path
import pickle
import os
import time

from scrapers.core import AuthorInfo
from scrapers.core import serialize, deserialize, create_folder_if_not_exists

from scrapers.semantic_scholar_scraper.semantic_scholar_api_call_manager import ApiCallManager
from scrapers.semantic_scholar_scraper.semantic_scholar_author import SemanticScholarAuthor
from scrapers.semantic_scholar_scraper.semantic_scholar_paper import SemanticScholarPaper
from scrapers.semantic_scholar_scraper.semantic_scholar_references import BaseReference, Citation, Reference
from scrapers.semantic_scholar_scraper.semantic_scholar_results import PaginatedResults

class SemanticScholarPaperInfo:
    """
    Stores information about a paper
    """
    def __init__(self):
        self.id = ""
        self.url = ""
        self.title = ""
        self.year = -1
        self.publication_date = None
        self.source = ""
        self.venue = ""
        self.openAccessPdf = ""


    def __str__(self):
        s = f"{self.id}\n"
        s += f"{self.url}\n"
        s += f"{self.title}\n"
        s += f"{self.year}\n"
        s += f"{self.source}\n"
        s += f"{self.venue}"
        return s

class SemanticScholarScraper:
    """
    This class retrieves data from Semantic Scholar API.
    """

    DEFAULT_API_URL = 'https://api.semanticscholar.org/graph/v1'
    DEFAULT_PARTNER_API_URL = 'https://partner.semanticscholar.org/graph/v1'

    auth_header = {}

    def __init__(
                self,
                timeout: int = 10,
                api_key: str = None,
                api_url: str = None,
                graph_api: bool = True
            ) -> None:
        '''
        :param float timeout: (optional) an exception is raised\
            if the server has not issued a response for timeout seconds.
        :param str api_key: (optional) private API key.
        :param str api_url: (optional) custom API url.
        :param bool graph_api: (optional) whether use new Graph API.
        '''

        if api_url:
            self.api_url = api_url
        else:
            self.api_url = self.DEFAULT_API_URL

        if api_key:
            self.auth_header = {'x-api-key': api_key}
            if not api_url:
                self.api_url = self.DEFAULT_PARTNER_API_URL

        if not graph_api:
            warnings.warn(
                'graph_api parameter is deprecated and will be disabled ' +
                'in the future', DeprecationWarning)
            self.api_url = self.api_url.replace('/graph', '')

        self._timeout = timeout
        self._requester = ApiCallManager(self._timeout)

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int) -> None:
        self._timeout = timeout
        self._requester.timeout = timeout

    def get_paper(
                self,
                paper_id: str,
                include_unknown_refs: bool = False,
                fields: list = None
            ) -> SemanticScholarPaper:
        '''Paper lookup

        :calls: `GET /paper/{paper_id} <https://api.semanticscholar.org/\
            api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper>`_

        :param str paper_id: S2PaperId, CorpusId, DOI, ArXivId, MAG, ACL, \
               PMID, PMCID, or URL from:

               - semanticscholar.org
               - arxiv.org
               - aclweb.org
               - acm.org
               - biorxiv.org

        :param bool include_unknown_refs: (optional) include non referenced \
               paper.
        :param list fields: (optional) list of the fields to be returned.
        :returns: paper data
        :rtype: :class:`semanticscholar.Paper.Paper`
        :raises: ObjectNotFoundExeception: if Paper ID not found.
        '''

        if not fields:
            fields = SemanticScholarPaper.FIELDS

        url = f'{self.api_url}/paper/{paper_id}'

        fields = ','.join(fields)
        parameters = f'&fields={fields}'
        if include_unknown_refs:
            warnings.warn(
                'include_unknown_refs parameter is deprecated and will be disabled ' +
                'in the future', DeprecationWarning)
            parameters += '&include_unknown_references=true'

        data = self._requester.get_data(url, parameters, self.auth_header)
        paper = SemanticScholarPaper(data)

        return paper

    def get_all_papers(
                self,
                paper_ids: List[str],
                fields: list = None
            ) -> List[SemanticScholarPaper]:
        '''Get details for multiple papers at once

        :calls: `POST /paper/batch <https://api.semanticscholar.org/api-docs/\
            graph#tag/Paper-Data/operation/post_graph_get_papers>`_

        :param str paper_ids: list of IDs (must be <= 1000) - S2PaperId,\
            CorpusId, DOI, ArXivId, MAG, ACL, PMID, PMCID, or URL from:

            - semanticscholar.org
            - arxiv.org
            - aclweb.org
            - acm.org
            - biorxiv.org

        :param list fields: (optional) list of the fields to be returned.
        :returns: papers data
        :rtype: :class:`List` of :class:`semanticscholar.Paper.Paper`
        :raises: BadQueryParametersException: if no paper was found.
        '''

        if not fields:
            fields = SemanticScholarPaper.SEARCH_FIELDS

        url = f'{self.api_url}/paper/batch'

        fields = ','.join(fields)
        parameters = f'&fields={fields}'

        payload = { "ids": paper_ids }

        data = self._requester.get_data(
            url, parameters, self.auth_header, payload)
        papers = [SemanticScholarPaper(item) for item in data]

        return papers

    def get_paper_authors(
                self,
                paper_id: str,
                fields: list = None,
                limit: int = 1000
            ) -> PaginatedResults:
        '''Get details about a paper's authors

        :calls: `POST /paper/{paper_id}/authors \
            <https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data\
            /operation/get_graph_get_paper_authors>`_

        :param str paper_id: S2PaperId, CorpusId, DOI, ArXivId, MAG, ACL,\
               PMID, PMCID, or URL from:

               - semanticscholar.org
               - arxiv.org
               - aclweb.org
               - acm.org
               - biorxiv.org

        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return\
               (must be <= 1000).
        '''

        if limit < 1 or limit > 1000:
            raise ValueError(
                'The limit parameter must be between 1 and 1000 inclusive.')

        if not fields:
            fields = [item for item in SemanticScholarAuthor.SEARCH_FIELDS
                      if not item.startswith('papers')]

        url = f'{self.api_url}/paper/{paper_id}/authors'

        results = PaginatedResults(
                requester=self._requester,
                data_type=Author,
                url=url,
                fields=fields,
                limit=limit
            )

        return results

    def get_paper_citations(
                self,
                paper_id: str,
                fields: list = None,
                limit: int = 1000
            ) -> PaginatedResults:
        '''Get details about a paper's citations

        :calls: `POST /paper/{paper_id}/citations \
            <https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data\
            /operation/get_graph_get_paper_citations>`_

        :param str paper_id: S2PaperId, CorpusId, DOI, ArXivId, MAG, ACL,\
               PMID, PMCID, or URL from:

               - semanticscholar.org
               - arxiv.org
               - aclweb.org
               - acm.org
               - biorxiv.org

        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return\
               (must be <= 1000).
        '''

        if limit < 1 or limit > 1000:
            raise ValueError(
                'The limit parameter must be between 1 and 1000 inclusive.')

        if not fields:
            fields = BaseReference.FIELDS + SemanticScholarPaper.SEARCH_FIELDS

        url = f'{self.api_url}/paper/{paper_id}/citations'

        results = PaginatedResults(
                requester=self._requester,
                data_type=Citation,
                url=url,
                fields=fields,
                limit=limit
            )

        return results

    def get_paper_references(
                self,
                paper_id: str,
                fields: list = None,
                limit: int = 1000
            ) -> PaginatedResults:
        '''Get details about a paper's references

        :calls: `POST /paper/{paper_id}/references \
            <https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data\
            /operation/get_graph_get_paper_references>`_

        :param str paper_id: S2PaperId, CorpusId, DOI, ArXivId, MAG, ACL,\
               PMID, PMCID, or URL from:

               - semanticscholar.org
               - arxiv.org
               - aclweb.org
               - acm.org
               - biorxiv.org

        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return\
               (must be <= 1000).
        '''

        if limit < 1 or limit > 1000:
            raise ValueError(
                'The limit parameter must be between 1 and 1000 inclusive.')

        if not fields:
            fields = BaseReference.FIELDS + SemanticScholarPaper.SEARCH_FIELDS

        url = f'{self.api_url}/paper/{paper_id}/references'

        results = PaginatedResults(
                requester=self._requester,
                data_type=Reference,
                url=url,
                fields=fields,
                limit=limit
            )

        return results

    def search_paper(
                self,
                query: str,
                year: str = None,
                publication_types: list = None,
                open_access_pdf: bool = None,
                venue: list = None,
                fields_of_study: list = None,
                fields: list = None,
                limit: int = 100
            ) -> PaginatedResults:
        '''Search for papers by keyword

        :calls: `GET /paper/search <https://api.semanticscholar.org/api-docs/\
            graph#tag/Paper-Data/operation/get_graph_get_paper_search>`_

        :param str query: plain-text search query string.
        :param str year: (optional) restrict results to the given range of \
               publication year.
        :param list publication_type: (optional) restrict results to the given \
               publication type list.
        :param bool open_access_pdf: (optional) restrict results to papers \
               with public PDFs.
        :param list venue: (optional) restrict results to the given venue list.
        :param list fields_of_study: (optional) restrict results to given \
               field-of-study list, using the s2FieldsOfStudy paper field.
        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return \
               (must be <= 100).
        :returns: query results.
        :rtype: :class:`semanticscholar.PaginatedResults.PaginatedResults`
        '''

        if limit < 1 or limit > 100:
            raise ValueError(
                'The limit parameter must be between 1 and 100 inclusive.')

        if not fields:
            fields = SemanticScholarPaper.SEARCH_FIELDS

        url = f'{self.api_url}/paper/search'

        query += f'&year={year}' if year else ''

        if publication_types:
            publication_types = ','.join(publication_types)
            query += f'&publicationTypes={publication_types}'

        query += '&openAccessPdf' if open_access_pdf else ''

        if venue:
            venue = ','.join(venue)
            query += f'&venue={venue}'

        if fields_of_study:
            fields_of_study = ','.join(fields_of_study)
            query += f'&fieldsOfStudy={fields_of_study}'

        results = PaginatedResults(
                self._requester,
                Paper,
                url,
                query,
                fields,
                limit,
                self.auth_header
            )

        return results

    def get_author(
                self,
                author_id: str,
                fields: list = None
            ) -> SemanticScholarAuthor:
        '''Author lookup

        :calls: `GET /author/{author_id} <https://api.semanticscholar.org/\
            api-docs/graph#tag/Author-Data/operation/get_graph_get_author>`_

        :param str author_id: S2AuthorId.
        :returns: author data
        :rtype: :class:`semanticscholar.Author.Author`
        :raises: ObjectNotFoundExeception: if Author ID not found.
        '''

        if not fields:
            fields = SemanticScholarAuthor.FIELDS

        url = f'{self.api_url}/author/{author_id}'

        fields = ','.join(fields)
        parameters = f'&fields={fields}'

        data = self._requester.get_data(url, parameters, self.auth_header)
        author = SemanticScholarAuthor(data)

        return author

    def get_authors(
                self,
                author_ids: List[str],
                fields: list = None
            ) -> List[SemanticScholarAuthor]:
        '''Get details for multiple authors at once

        :calls: `POST /author/batch <https://api.semanticscholar.org/api-docs/\
            graph#tag/Author-Data/operation/get_graph_get_author>`_

        :param str author_ids: list of S2AuthorId (must be <= 1000).
        :returns: author data
        :rtype: :class:`List` of :class:`semanticscholar.Author.Author`
        :raises: BadQueryParametersException: if no author was found.
        '''

        if not fields:
            fields = SemanticScholarAuthor.SEARCH_FIELDS

        url = f'{self.api_url}/author/batch'

        fields = ','.join(fields)
        parameters = f'&fields={fields}'

        payload = { "ids": author_ids }

        data = self._requester.get_data(url, parameters, self.auth_header, payload)
        authors = [SemanticScholarAuthor(item) for item in data]

        return authors

    def get_author_papers(
                self,
                author_id: str,
                fields: list = None,
                limit: int = 1000
            ) -> PaginatedResults:
        '''Get details about a author's papers

        :calls: `POST /paper/{author_id}/papers \
            <https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data\
            /operation/get_graph_get_author_papers>`_

        :param str paper_id: S2PaperId, CorpusId, DOI, ArXivId, MAG, ACL,\
               PMID, PMCID, or URL from:

               - semanticscholar.org
               - arxiv.org
               - aclweb.org
               - acm.org
               - biorxiv.org

        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return\
               (must be <= 1000).
        '''

        if limit < 1 or limit > 1000:
            raise ValueError(
                'The limit parameter must be between 1 and 1000 inclusive.')

        if not fields:
            fields = SemanticScholarPaper.SEARCH_FIELDS

        url = f'{self.api_url}/author/{author_id}/papers'

        results = PaginatedResults(
                requester=self._requester,
                data_type=SemanticScholarPaper,
                url=url,
                fields=fields,
                limit=limit
            )

        return results

    def search_author(
                self,
                query: str,
                fields: list = None,
                limit: int = 1000
            ) -> PaginatedResults:
        '''Search for authors by name

        :calls: `GET /author/search <https://api.semanticscholar.org/api-docs/\
            graph#tag/Author-Data/operation/get_graph_get_author_search>`_

        :param str query: plain-text search query string.
        :param list fields: (optional) list of the fields to be returned.
        :param int limit: (optional) maximum number of results to return \
               (must be <= 1000).
        :returns: query results.
        :rtype: :class:`semanticscholar.PaginatedResults.PaginatedResults`
        '''

        if limit < 1 or limit > 1000:
            raise ValueError(
                'The limit parameter must be between 1 and 1000 inclusive.')

        if not fields:
            fields = SemanticScholarAuthor.SEARCH_FIELDS

        url = f'{self.api_url}/author/search'

        results = PaginatedResults(
                self._requester,
                SemanticScholarAuthor,
                url,
                query,
                fields,
                limit,
                self.auth_header
            )
        return results

    @staticmethod
    def is_a_match(first: str, second: str):
        """Checks if two author names are a match"""
        if first == None or second == None:
            return False
        parsed_first = first.split(" ")
        parsed_second = second.split(" ")
        if len(parsed_first) <= 1 or len(parsed_second) <= 1:
            return False
        name_first = parsed_first[0].strip()
        surname_first = parsed_first[-1].strip()
        name_second = parsed_second[0].strip()
        surname_second = parsed_second[-1].strip()
        if name_first.lower() == name_second.lower() and surname_first.lower() == surname_second.lower():
            return True
        if name_first[0].lower() == name_second[0].lower() and surname_first.lower() == surname_second.lower():
            return True
        return False

    @staticmethod
    def standardize_name_word(name: str):
        s = name.lower()
        if len(name) == 1:
            s += "."
        return s

    @staticmethod
    def standardize_name(full_name: str):
        parsed = full_name.split(" ")
        result = []
        for token in parsed:
            result.append(SemanticScholarScraper.standardize_name_word(token))
        return result

    @staticmethod
    def permute(full_name: str):
        std = SemanticScholarScraper.standardize_name_word(full_name)
        parsed = std.split(" ")
        permutations = []
        if len(parsed) < 1:
            return False, permutations
        permutations.extend(list(itertools.permutations(parsed)))
        for token in parsed:
            if len(token) == 2 and token.endswith("."):
                continue
            modified = f"{token[0]}."
            arr = []
            for item in parsed:
                if item == token:
                    arr.append(modified)
                else:
                    arr.append(item)
            permutations.extend(list(itertools.permutations(arr)))

        parsed_modified = []
        irregular = False
        for token in parsed:
            if (len(token) == 2 and token.endswith(".")) or len(token) == 1:
                irregular = True
                continue
            parsed_modified.append(token)

        if irregular:
            permutations.extend(list(itertools.permutations(parsed_modified)))
            for token in parsed_modified:
                modified = f"{token[0]}."
                arr = []
                for item in parsed_modified:
                    if item == token:
                        arr.append(modified)
                    else:
                        arr.append(item)
                permutations.extend(list(itertools.permutations(arr)))

        final = set()
        for item in permutations:
            final.add(" ".join(item))
        return True, final

    @staticmethod
    def get_author_id_list(name: str, surname: str):
        """Returns a list of author ids for a given name and surname"""
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={name}+{surname}"
        response = requests.get(search_url)
        results = response.json()["data"]
        lst = []
        for result in results:
            current_name = result["name"]
            if name in current_name and surname in current_name:
                lst.append(result["authorId"])
            if name[0] in current_name and surname in current_name:
                lst.append(result["authorId"])
        return lst


        # returned_names = set()
        # name_to_id = {}
        # for result in results:
        #     modified = result["name"].lower()
        #     returned_names.add(modified)
        #     name_to_id[modified] = result["authorId"]
        # #print(name_to_id)
        # lst = []
        # valid, permutations = SemanticScholarScraper.permute(f"{name} {surname}")
        # if not valid:
        #     return lst
        # common = returned_names & permutations
        #
        # if len(common) > 0:
        #     for name in common:
        #         lst.append(name_to_id[name])
        # return lst

    @staticmethod
    def test_access_author_id(name: str, surname: str):
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={name}+{surname}"
        response = requests.get(search_url)
        results = response.json()["data"]
        return results

    def test_get_author_id_list(self):
        lst = SemanticScholarScraper.get_author_id_list("Usama", "Fayyad")
        print(lst)

    @staticmethod
    def get_papers_by_time_interval(author_id: str, start_date: datetime, end_date: datetime):
        """Returns a list of papers for a given author id and a given time period"""
        start_year = start_date.year
        end_year = end_date.year
        #search_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}?fields=affiliations"
        search_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,url,year,publicationDate,venue,publicationVenue,openAccessPdf&limit=1000"
        response = requests.get(search_url)
        papers = response.json()["data"]
        output = []
        for paper in papers:
            if "year" in paper and paper["year"] != None:
                info = SemanticScholarPaperInfo()
                if "publicationDate" in paper and paper["publicationDate"] != None:
                    info.publication_date = datetime.strptime(paper["publicationDate"], "%Y-%m-%d")
                info.year = paper["year"]
                if info.publication_date is not None:
                    if info.publication_date.year < start_year or info.publication_date.year > end_year:
                        continue
                else:
                    if info.year < start_year or info.year > end_year:
                        continue
                info.id = paper["paperId"]
                info.url = paper["url"]
                info.title = paper["title"]
                info.source = paper["venue"]
                if paper["publicationVenue"] != None:
                    if "type" in paper["publicationVenue"]:
                        info.venue = paper["publicationVenue"]["type"]
                    elif info.source == "arXiv.org":
                        info.venue = "arXiv"

                if "openAccessPdf" in paper:
                    info.openAccessPdf = paper["openAccessPdf"]
                output.append(info)
            # info = SemanticScholarPaperInfo()
            # info.year = paper["year"]
            # info.id = paper["paperId"]
            # info.url = paper["url"]
            # info.title = paper["title"]
            # info.source = paper["venue"]
            # if paper["publicationVenue"] != None:
            #     if "type" in paper["publicationVenue"]:
            #         info.venue = paper["publicationVenue"]["type"]
            #     elif info.source == "arXiv.org":
            #         info.venue = "arXiv"
            # output.append(info)
        return output

    @staticmethod
    def get_papers_by_name_surname_by_interval(name: str, surname: str, start_date: datetime, end_date: datetime):
        """Returns a list of papers for a given author name and surname and a given time period"""
        author_id_list = SemanticScholarScraper.get_author_id_list(name, surname)
        results = []
        for id in author_id_list:
            papers =  SemanticScholarScraper.get_papers_by_time_interval(id, start_date, end_date)
            for paper in papers:
                results.append(paper)
        return results

    @staticmethod
    def get_papers_by_author_by_interval(full_name: str, eai_url: str, start_date: datetime, end_date: datetime):
        start_year = start_date.year
        end_year = end_date.year
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()
        info_array = SemanticScholarScraper.get_papers_by_name_surname_by_interval(name, surname, start_date, end_date)
        output = {}
        output = []
        for info in info_array:
            paper_info = AuthorInfo(full_name, eai_url)
            paper_info.link = info.url
            paper_info.publication_date = datetime(info.year, 1, 1)
            paper_info.title = info.title
            paper_info.data_source = "Semantic Scholar"
            paper_info.publication = info.source
            paper_info.type = info.venue
            paper_info.eai_match = False

            output.append(paper_info)
        return output

    @staticmethod
    def test_get_papers_by_author():
        output = SemanticScholarScraper.get_papers_by_author_by_interval("Usama Fayyad",
                                                              "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
                                                              datetime(2023, 1, 1), datetime(2023, 12, 31))
        for k, v in output.items():
            print(f"Author: {k}, Number of papers: {len(v)}")
        for k, v in output.items():
            for item in v:
                print(item)

    @staticmethod
    def get_papers(author_names_and_urls: [], start_date: datetime, end_date: datetime, target_folder: str):
        """
        This method returns a list of AuthorInfo objects for the given authors.
        :param author_names:
        :param data:
        :param start_date:
        :param end_date:
        :return:
        """
        papers = []
        count = 0
        for pair in author_names_and_urls:
            full_name = pair[0]
            eai_url = pair[1]
            try:
                papers_by_author = SemanticScholarScraper.get_papers_by_author_by_interval(full_name, eai_url, start_date, end_date)
                print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
                papers.extend(papers_by_author)
                time.sleep(5)
                # count += 1
                # if count >= 2:
                #     break
            except Exception as e:
                print(f"Error processing {pair[0]}:")
                print(e)
                time.sleep(10)

        for paper in papers:
            title = paper.title.replace("\n", "").replace("\t", "")
            print(f"{paper.full_name};{title};{paper.data_source};{paper.type};{paper.link}")

        script_path = Path(__file__).resolve()
        base_dir = script_path.parent.parent
        pkl_folder = os.path.join(base_dir, target_folder)
        create_folder_if_not_exists(pkl_folder)
        serialize(papers, os.path.join(pkl_folder, 'semantic_scholar.pkl'))


    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        output = \
            SemanticScholarScraper.get_papers(author_names_and_urls, datetime(2023, 11, 1), datetime(2023, 12, 31), "pkl_files")

# start_date = datetime(2023, 1, 1)
# end_date = datetime(2023, 12, 31)
# papers_by_author = SemanticScholarScraper.get_papers_by_author_by_interval("Jennifer G Dy", "", start_date, end_date)
# print(len(papers_by_author))






