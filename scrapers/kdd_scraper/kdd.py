import requests
from bs4 import BeautifulSoup
from datetime import datetime

class KddPaperInfo:

    def __init__(self):
        self.html_link = ""
        self.title = ""
        self.authors = []

    def __str__(self):
        s = f"{self.html_link}\n"
        s += f"{self.title}\n"
        for author in self.authors:
            s += f"{author}, "
        return s

class KddScraper():

    def __init__(self):
        pass

    @staticmethod
    def get_papers_by_authors(start_date: datetime , end_date: datetime):
        start_year = start_date.year
        end_year = end_date.year
        papers_by_author = {}
        for year in range(start_year, end_year + 1):
            url  = f"https://papers.nips.cc/paper_files/paper/{year}"
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find all the links in the page
                links = soup.find_all('li', class_="conference")
                # Loop through the links and print the ones that seems to represent papers
                for link in links:
                    r0 = link.find_all('a')
                    href = r0[0].get('href')
                    kdd_paper_info = KddPaperInfo()
                    if '/paper/' in href:
                        kdd_paper_info.html_link = f"https://papers.nips.cc{href}"
                        kdd_paper_info.title = r0[0].text
                        r1 = link.find_all('i')
                        parsed = r1[0].text.split(',')
                        for author in parsed:
                            stripped = author.strip()
                            kdd_paper_info.authors.append(stripped)
                            if stripped not in papers_by_author:
                                papers_by_author[stripped] = []
                            papers_by_author[stripped].append(kdd_paper_info)
            else:
                print(f'Failed to retrieve the webpage: {year}')
        return papers_by_author

# output = KddScraper.get_papers_by_authors(datetime(1980, 1, 1), datetime(2023, 12, 31))
# for author, papers in output.items():
#     print(f"{author}: {len(papers)}")