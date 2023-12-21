import urllib.request as libreq
import urllib
import requests
import feedparser
from datetime import datetime

from scrapers.core import AuthorInfo
from scrapers.semantic_scholar_scraper.semantic_scholar_scraper import SemanticScholarScraper

class SemanticScholarPaperInfo:
    """
    Stores information about a paper
    """
    def __init__(self):
        self.id = ""
        self.url = ""
        self.title = ""
        self.year = -1
        self.source = ""
        self.venue = ""

    def __str__(self):
        s = f"{self.id}\n"
        s += f"{self.url}\n"
        s += f"{self.title}\n"
        s += f"{self.year}\n"
        s += f"{self.source}\n"
        s += f"{self.venue}"
        return s

def is_a_match(first: str, second: str):
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

def get_author_id_list(name: str, surname: str):
    search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={name}+{surname}"
    response = requests.get(search_url)
    results = response.json()["data"]
    lst = []
    for result in results:
        if is_a_match(result["name"], f"{name} {surname}"):
            lst.append(result["authorId"])
    return lst

def get_papers(author_id: str):
    search_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,url,year,venue,publicationVenue&limit=1000"
    response = requests.get(search_url)
    papers = response.json()["data"]
    output = []
    for paper in papers:
        info = SemanticScholarPaperInfo()
        info.id = paper["paperId"]
        info.url = paper["url"]
        info.title = paper["title"]
        info.source = paper["venue"]
        info.year = paper["year"]
        if paper["publicationVenue"] != None:
            if "type" in paper["publicationVenue"]:
                info.venue = paper["publicationVenue"]["type"]
            elif info.source == "arXiv.org":
                info.venue = "arXiv"
        output.append(info)
    return output

def get_papers_by_year(author_id: str, start_date: datetime, end_date: datetime):
    start_year = start_date.year
    end_year = end_date.year
    search_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,url,year,venue,publicationVenue&limit=1000"
    response = requests.get(search_url)
    papers = response.json()["data"]
    output = []
    for paper in papers:
        if "year" in paper and paper["year"] != None:
            info = SemanticScholarPaperInfo()
            info.year = paper["year"]
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

def get_papers_by_author(name: str, surname: str):
    author_id_list = get_author_id_list(name, surname)
    results = []
    for id in author_id_list:
        papers = get_papers(id)
        for paper in papers:
            results.append(paper)
    return results

def get_papers_by_author_by_interval(name: str, surname: str, start_date: datetime, end_date: datetime):
    author_id_list = get_author_id_list(name, surname)
    results = []
    for id in author_id_list:
        papers = get_papers_by_year(id, start_date, end_date)
        for paper in papers:
            results.append(paper)
    return results

def get_papers_by_authors_by_interval(author_full_name_list: [], start_date: datetime, end_date: datetime):
    for pair in author_full_name_list:
        full_name = pair[0]
        eai_url = pair[1]
        parsed = full_name.split(" ")
        if len(parsed) <= 1:
            continue
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()
        papers = get_papers_by_author_by_interval(name, surname, start_date, end_date)
        output = []
        for paper in papers:
            author_info = AuthorInfo(name, surname, eai_url)
            author_info.link = paper.url
            author_info.year = paper.year
            author_info.title = paper.title
            author_info.source = paper.source
            author_info.venue = paper.venue
            output.append(author_info)
        return output



# papers = get_papers("152313541")
# for paper in papers:
#     print(paper)
#     print()

# papers = get_papers_by_author("Eduardo", "Sontag")
# #papers = get_papers_by_author_by_interval("Eduardo", "Sontag", datetime(1900, 1, 1), datetime(2023, 12, 31))
# print(len(papers))

papers = SemanticScholarScraper.get_papers_by_author("Eduardo", "Sontag")
#papers = get_papers_by_author_by_interval("Eduardo", "Sontag", datetime(1900, 1, 1), datetime(2023, 12, 31))
print(len(papers))


