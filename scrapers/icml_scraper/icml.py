import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from scrapers.core import AuthorInfo


class IcmlPaperInfo:
    """
    Stores information about a paper
    """
    def __init__(self):
        self.html_link = ""
        self.pdf_link = ""
        self.title = ""
        self.authors = []
        self.year = -1
        self.source = ""

    def __str__(self):
        s = f"{self.html_link}\n"
        s += f"{self.title}\n"
        s += f"{self.year}\n"
        for author in self.authors:
            s += f"{author}, "
        return s

def get_conference_name_and_year(title: str):
    """
    Extracts the conference name and year from the title of the paper
    :param title:
    :return:
    """
    # Text string containing the title of the paper
    # Regular expression pattern to match the conference name and year
    pattern1 = re.compile(r'Volume\s+\d+:\s+(.*),\s+\d{1,2}-\d{1,2}\s+.*\s+(\d{4})')
    pattern2 = re.compile(r'Volume\s+\d+:\s+(.*),\s+\d{1,2}\s+.*\s+(\d{4})')

    # Search the text for the pattern
    match1 = pattern1.search(title)
    match2 = pattern2.search(title)

    # Extract and print the conference name and year
    if match1:
        conference_name = match1.group(1)
        year = match1.group(2)
        return conference_name, year
    elif match2:
        conference_name = match2.group(1)
        year = match2.group(2)
        return conference_name, year
    else:
        return None, None

class IcmlScraper():
    """
    Scrapes the ICML website for papers
    """
    def __init__(self):
        pass

    @staticmethod
    def get_papers_by_authors(max_volume: int):
        """
        Gets the papers by authors
        :param max_volume:
        :return:
        """
        papers_by_author = {}
        for volume in range(1, max_volume + 1):
            print(f"Volume: {volume}")
            url  = f"http://proceedings.mlr.press/v{volume}"
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                header = soup.find_all('h2')
                header_text = header[0].text
                conference_name, year = get_conference_name_and_year(header_text)
                if conference_name is None or year is None:
                    print(f"Failed to retrieve the volume: {year} since conference year could not be accessed")
                    continue

                # Find all paper entries
                paper_entries = soup.find_all('div', class_='paper')

                # Loop through each paper entry
                for paper in paper_entries:
                    # Find the link to the paper
                    r1 = paper.find_all('p', class_='title')
                    r2 = paper.find_all('p', class_='details')
                    r3 = r2[0].find_all('span', class_='authors')
                    r4 = paper.find_all('p', class_='links')
                    r5 = r4[0].find_all('a')

                    icml_paper_info = IcmlPaperInfo()
                    icml_paper_info.title = r1[0].text
                    icml_paper_info.html_link = r5[0].get('href')
                    if len(r5) > 1:
                        icml_paper_info.pdf_link = r5[1].get('href')
                    icml_paper_info.source = conference_name
                    icml_paper_info.year = int(year)
                    parsed = r3[0].text.split(',')
                    for author in parsed:
                        stripped = author.strip().lower()
                        icml_paper_info.authors.append(stripped)
                        if stripped not in papers_by_author:
                            papers_by_author[stripped] = []
                        papers_by_author[stripped].append(icml_paper_info)
            else:
                print(f'Failed to retrieve the volume: {year} since it does not exist')
        return papers_by_author

    @staticmethod
    def get_papers_by_author(name: str, surname: str, eai_url: str, data: {}, start_date: datetime, end_date: datetime):
        """
        Returns a list of AuthorInfo objects for the given author
        :param name:
        :param surname:
        :param eai_url:
        :param data:
        :param start_date:
        :param end_date:
        :return:
        """
        full_name = f"{name} {surname}"
        parsed_name = full_name.split(' ')
        author_info_list = []
        start_year = start_date.year
        end_year = end_date.year
        for author_name, papers in data.items():
            parsed_author_name = author_name.split(' ')
            if IcmlScraper.is_a_match_symmetric(parsed_name, parsed_author_name):
                for paper in papers:
                    if paper.year >= start_year and paper.year <= end_year:
                        author_info = AuthorInfo(name, surname, eai_url)
                        author_info.link = paper.html_link
                        author_info.pdf_link = paper.pdf_link
                        author_info.title = paper.title
                        author_info.publication_date = datetime(paper.year, 1, 1)
                        author_info.source = paper.source
                        author_info.venue = "Conference"
                        author_info_list.append(author_info)
        return author_info_list

    @staticmethod
    def get_papers(author_names: [], data: {}, start_date: datetime, end_date: datetime):
        """
        Returns a list of AuthorInfo objects for the given author
        :param author_names:
        :param data:
        :param start_date:
        :param end_date:
        :return:
        """
        papers = []
        for author_name in author_names:
            papers_by_author = IcmlScraper.get_papers_by_author(author_name, data, start_date, end_date)
            papers.extend(papers_by_author)
        return papers

    @staticmethod
    def is_a_match(first: [], second: []):
        """
        Checks if the first list is a subset of the second list
        :param first:
        :param second:
        :return:
        """
        for name in first:
            if name.lower() not in second:
                return False
        return True

    @staticmethod
    def is_a_match_symmetric(first: [], second: []):
        """
        Checks if the first list is a subset of the second list
        :param first:
        :param second:
        :return:
        """
        return IcmlScraper.is_a_match(first, second) or IcmlScraper.is_a_match(second, first)

# output = IcmlScraper.get_papers_by_authors(220)
# for author, papers in output.items():
#     print(f"{author}: {len(papers)}")

# data = IcmlScraper.get_papers_by_authors(220)
# output = IcmlScraper.get_papers_by_author("jean-jacques", "slotine", " ", data, datetime(1980, 1, 1), datetime(2023, 12, 31))
# for item in output:
#     print(item)



