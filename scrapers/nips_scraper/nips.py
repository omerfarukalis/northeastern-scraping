import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers.core import AuthorInfo
import os

class NipsPaperInfo:
    """
    This class represents a paper from the NIPS conference.
    """
    def __init__(self):
        self.html_link = ""
        self.title = ""
        self.authors = []
        self.year = -1

    def __str__(self):
        s = f"{self.html_link}\n"
        s += f"{self.title}\n"
        s += f"{self.year}\n"
        for author in self.authors:
            s += f"{author}, "
        return s

class NipsScraper():

    def __init__(self):
        pass

    @staticmethod
    def is_a_match(first: [], second: []):
        """
        This method checks if the first list of names is contained in the second list of names.
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
        This method checks if the first list of names is contained in the second list of names or vice versa.
        :param first:
        :param second:
        :return:
        """
        return NipsScraper.is_a_match(first, second) or NipsScraper.is_a_match(second, first)

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

    # @staticmethod
    # def get_papers_by_year(year: int):
    #     """
    #     This method returns a dictionary where the keys are the authors and the values are the papers they have written.
    #     :param year:
    #     :return:
    #     """
    #     papers_by_author = {}
    #     url = f"https://papers.nips.cc/paper_files/paper/{year}"
    #     response = requests.get(url)
    #     # Check if the request was successful
    #     if response.status_code == 200:
    #         # Parse the HTML content
    #         soup = BeautifulSoup(response.text, 'html.parser')
    #         # Find all the links in the page
    #         links = soup.find_all('li', class_="none")
    #         # Loop through the links and print the ones that seems to represent papers
    #         for link in links:
    #             r0 = link.find_all('a')
    #             href = r0[0].get('href')
    #             nips_paper_info = NipsPaperInfo()
    #             if '/paper/' in href:
    #                 nips_paper_info.html_link = f"https://papers.nips.cc{href}"
    #                 nips_paper_info.title = r0[0].text
    #                 nips_paper_info.year = year
    #                 r1 = link.find_all('i')
    #                 parsed = r1[0].text.split(',')
    #                 for author in parsed:
    #                     stripped = author.strip().lower()
    #                     nips_paper_info.authors.append(stripped)
    #                     if stripped not in papers_by_author:
    #                         papers_by_author[stripped] = []
    #                     papers_by_author[stripped].append(nips_paper_info)
    #     else:
    #         print(f'Failed to retrieve the webpage: {year}')
    #     return papers_by_author

    @staticmethod
    def get_papers_by_year(year: int):
        """
        This method returns a dictionary where the keys are the authors and the values are the papers they have written.
        :param year:
        :return:
        """
        papers_by_author = {}
        url = f"https://papers.nips.cc/paper_files/paper/{year}"
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all the links in the page
            ul = soup.find('ul', class_="paper-list")
            links = ul.find_all('li')
            # Loop through the links and print the ones that seems to represent papers
            for link in links:
                r0 = link.find_all('a')
                href = r0[0].get('href')
                nips_paper_info = NipsPaperInfo()
                if '/paper/' in href:
                    nips_paper_info.html_link = f"https://papers.nips.cc{href}"
                    nips_paper_info.title = r0[0].text
                    nips_paper_info.year = year
                    r1 = link.find_all('i')
                    parsed = r1[0].text.split(',')
                    for author in parsed:
                        stripped = author.strip().lower()
                        nips_paper_info.authors.append(stripped)
                        if stripped not in papers_by_author:
                            papers_by_author[stripped] = []
                        papers_by_author[stripped].append(nips_paper_info)
        else:
            print(f'Failed to retrieve the webpage: {year}')
        return papers_by_author

    @staticmethod
    def test_get_papers_by_year(year: int):
        output = NipsScraper.get_papers_by_year(year)
        for author, papers in output.items():
            for paper in papers:
                print(f"{author}, {paper.html_link}, {paper.title}")

    @staticmethod
    def get_papers_by_interval(start_date: datetime, end_date: datetime):
        """
        This method returns a dictionary where the keys are the authors and the values are the papers they have written.
        :param start_date:
        :param end_date:
        :return:
        """
        start_year = start_date.year
        end_year = end_date.year
        papers_by_author = {}
        for year in range(start_year, end_year + 1):
            print(f"Processing year: {year}")
            current_data = NipsScraper.get_papers_by_year(year)
            for author, papers in current_data.items():
                if author not in papers_by_author:
                    papers_by_author[author] = []
                papers_by_author[author].extend(papers)
        return papers_by_author

    # @staticmethod
    # def get_papers_by_authors(start_date: datetime , end_date: datetime):
    #     """
    #     This method returns a dictionary where the keys are the authors and the values are the papers they have written.
    #     :param start_date:
    #     :param end_date:
    #     :return:
    #     """
    #     start_year = start_date.year
    #     end_year = end_date.year
    #     papers_by_author = {}
    #     for year in range(start_year, end_year + 1):
    #         url  = f"https://papers.nips.cc/paper_files/paper/{year}"
    #         # Send a GET request to the URL
    #         response = requests.get(url)
    #
    #         # Check if the request was successful
    #         if response.status_code == 200:
    #             # Parse the HTML content
    #             soup = BeautifulSoup(response.text, 'html.parser')
    #             # Find all the links in the page
    #             links = soup.find_all('li', class_="conference")
    #             # Loop through the links and print the ones that seems to represent papers
    #             for link in links:
    #                 r0 = link.find_all('a')
    #                 href = r0[0].get('href')
    #                 nips_paper_info = NipsPaperInfo()
    #                 if '/paper/' in href:
    #                     nips_paper_info.html_link = f"https://papers.nips.cc{href}"
    #                     nips_paper_info.title = r0[0].text
    #                     nips_paper_info.year = year
    #                     r1 = link.find_all('i')
    #                     parsed = r1[0].text.split(',')
    #                     for author in parsed:
    #                         stripped = author.strip().lower()
    #                         nips_paper_info.authors.append(stripped)
    #                         if stripped not in papers_by_author:
    #                             papers_by_author[stripped] = []
    #                         papers_by_author[stripped].append(nips_paper_info)
    #         else:
    #             print(f'Failed to retrieve the webpage: {year}')
    #     return papers_by_author

    @staticmethod
    def get_papers_by_author(name: str, surname: str, eai_url: str, data: {}, start_date: datetime, end_date: datetime):
        """
        This method returns a list of AuthorInfo objects for the given author.
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
            if NipsScraper.is_a_match_symmetric(parsed_name, parsed_author_name):
                for paper in papers:
                    if paper.year >= start_year and paper.year <= end_year:
                        author_info = AuthorInfo(name, surname, eai_url)
                        author_info.link = paper.html_link
                        author_info.title = paper.title
                        author_info.publication_date = datetime(paper.year, 1, 1)
                        author_info.source = "NIPS"
                        author_info.venue = "Conference"
                        author_info.type = "conference"
                        author_info_list.append(author_info)
        return author_info_list

        # self.full_name = full_name
        # self.eai_url = eai_url
        # self.link = ""
        # self.pdf_link = ""
        # self.publication_date = None
        # self.data_source = ""
        # self.publication = ""
        # self.title = ""
        # self.eai_match = False
        # self.affiliation = ""
        # self.type = ""
        # self.citations = 0

    @staticmethod
    def get_papers(author_names_and_urls: [], start_date: datetime, end_date: datetime):
        """
        This method returns a list of AuthorInfo objects for the given authors.
        :param author_names:
        :param data:
        :param start_date:
        :param end_date:
        :return:
        """
        data = NipsScraper.get_papers_by_interval(start_date, end_date)
        papers = []
        for author_name in author_names:
            papers_by_author = NipsScraper.get_papers_by_author(author_name, data, start_date, end_date)
            papers.extend(papers_by_author)
        return papers


    @staticmethod
    def test_get_papers_by_author():
        start_date = datetime(2000, 1, 1)
        end_date = datetime(2023, 12, 31)
        data = NipsScraper.get_papers_by_interval(start_date, end_date)
        papers = NipsScraper.get_papers_by_author("Jennifer G. Dy", "https://ai.northeastern.edu/ai-our-people/jennifer-dy/", data, start_date, end_date)
        for paper in papers.values():
            print(f"{paper.full_name}, {paper.link}, {paper.type}, {paper.publication}")

    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        output = NipsScraper.get_papers(author_names_and_urls, datetime(2023, 1, 1), datetime(2023, 12, 31))


#NipsScraper.test_get_papers_by_author()