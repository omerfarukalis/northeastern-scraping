import urllib.request as libreq
import urllib
import requests
import feedparser
import pandas as pd
from datetime import datetime
from scrapers.core import AuthorInfo
from scrapers.core import serialize, deserialize, create_folder_if_not_exists

from pathlib import Path
import pickle
import os
import time




class ArxivScraper:
    @staticmethod
    def access_test_01():
        url = 'http://export.arxiv.org/api/query?search_query=au:usama+AND+fayyad&start=0&max_results=10'
        data = urllib.request.urlopen(url)
        print(data.read().decode('utf-8'))
        # d = feedparser.parse(response_search.content.decode('utf-8'))
        # #print(d.entries[0])
        # print(response_search.content.decode('utf-8'))

    @staticmethod
    def access_test_02():
        with libreq.urlopen('http://export.arxiv.org/api/query?search_query=au:xiao&start=0&max_results=100') as url:
            r = url.read()
        print(r.decode('utf-8'))


    @staticmethod
    def get_papers_by_author_by_interval(full_name: str, eai_url: str, start_date: datetime, end_date: datetime):
        """
        This method returns a list of AuthorInfo objects for the given author.
        :param full_name:
        :param eai_url:
        :param start_date:
        :param end_date:
        :return:
        """
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()
        token = f"{name}+AND+{surname}"
        search_url = f"http://export.arxiv.org/api/query?search_query=au:{token}&start=0&max_results=1000"
        response = requests.get(search_url)
        status_code = response.status_code
        output = []
        if status_code == 200:
            data = feedparser.parse(response.content.decode('utf-8'))
            if len(data) == 0:
                return output
            for item in data.entries:
                author = AuthorInfo(full_name, eai_url)
                author.link = item["id"]
                author.publication_date = datetime.strptime(item["updated"], '%Y-%m-%dT%H:%M:%SZ')
                if author.publication_date < start_date or author.publication_date > end_date:
                    continue
                author.data_source = "arxiv"
                author.title = item["title"]
                author.eai_match = False
                author.publication = "arxiv"
                author.type = "pre-print"
                for l in item["links"]:
                    if "title" in l:
                        if l["title"] == "pdf":
                            author.pdf_link = l["href"]
                        break
                output.append(author)
        else:
            time.sleep(60)
        return output

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
                papers_by_author = ArxivScraper.get_papers_by_author_by_interval(full_name, eai_url, start_date, end_date)
                print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
                papers.extend(papers_by_author)
                time.sleep(1)
                # count += 1
                # if count >= 2:
                #     break
            except Exception as e:
                print(f"Error processing {pair[0]}:")
                print(e)
                time.sleep(120)

        for paper in papers:
            title = paper.title.replace("\n", "").replace("\t", "")
            print(f"{paper.full_name};{title};{paper.publication_date};{paper.pdf_link}")

        script_path = Path(__file__).resolve()
        base_dir = script_path.parent.parent
        pkl_folder = os.path.join(base_dir, target_folder)
        create_folder_if_not_exists(pkl_folder)
        serialize(papers, os.path.join(pkl_folder, 'arxiv.pkl'))

    @staticmethod
    def test_get_papers_by_author():
        papers = ArxivScraper.get_papers_by_author_by_interval("Jennifer G. Dy", "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
                                                               datetime(2023, 1, 1), datetime(2023, 12, 31))
        print(len(papers))

    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        ArxivScraper.get_papers(author_names_and_urls,datetime(2023, 11, 1), datetime(2023, 12, 31), "pkl_files")


#ArxivScraper.access_test_01()

#ArxivScraper.test_get_papers_by_author()

#ArxivScraper.test_get_papers()