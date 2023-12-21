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
import openpyxl


NYTIMES_API_KEY = '3IcwkQGEBgSRBENfiZzvvlEIgqZyJj5R'
class NyTimesScraper:
    @staticmethod
    def access_test_01():
        nytimes_api_key = '3IcwkQGEBgSRBENfiZzvvlEIgqZyJj5R'
        search_url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q=beth+noveck&&api-key={nytimes_api_key}&begin_date=20230101&end_date=20231231"
        response = requests.get(search_url)
        status_code = response.status_code
        print(status_code)

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
        token = f"{name}+AND+{surname}+Northeastern+University"
        f_start_date = start_date.strftime('%Y%m%d')
        f_end_date = end_date.strftime('%Y%m%d')

        search_url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={token}&&api-key={NYTIMES_API_KEY}&" \
                     f"begin_date={f_start_date}&end_date={f_end_date}"
        response = requests.get(search_url)
        status_code = response.status_code
        output = []
        if status_code == 200:
            docs = response.json()["response"]["docs"]
            if len(docs) == 0:
                return output
            for item in docs:
                article = AuthorInfo(full_name, eai_url)
                article.link = item["web_url"]
                article.publication_date = datetime.strptime(item["pub_date"], '%Y-%m-%dT%H:%M:%S%z')
                article.data_source = item["source"]
                article.title = item["abstract"]
                article.eai_match = False
                article.publication = "The New York Times"
                article.type = "news article"
                output.append(article)
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
                papers_by_author = NyTimesScraper.get_papers_by_author_by_interval(full_name, eai_url, start_date, end_date)
                print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
                papers.extend(papers_by_author)
                time.sleep(10)
                # count += 1
                # if count >= 2:
                #     break
            except Exception as e:
                print(f"Error processing {pair[0]}:")
                print(e)
                time.sleep(120)

        for paper in papers:
            print(paper)
        # script_path = Path(__file__).resolve()
        # base_dir = script_path.parent.parent
        # pkl_folder = os.path.join(base_dir, target_folder)
        # create_folder_if_not_exists(pkl_folder)
        # serialize(papers, os.path.join(pkl_folder, 'nytimes.pkl'))

    @staticmethod
    def test_get_papers_by_author():
        papers = NyTimesScraper.get_papers_by_author_by_interval("Beth Noveck", "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
                                                               datetime(2023, 1, 1), datetime(2023, 12, 31))
        print(len(papers))

    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        NyTimesScraper.get_papers(author_names_and_urls,datetime(2018, 1, 1), datetime(2023, 12, 31), "pkl_files")

# nytimes_api_key = '3IcwkQGEBgSRBENfiZzvvlEIgqZyJj5R'
# fq="source:(\"Usama Fayyad\", \"usama fayyad\")"
# fq="organizations.contains:(\"NorthEastern University\") AND pub_year:(\"2023\")"
# fq="pub_date:(\"2023-01-30\")"
# search_url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q=beth+noveck&&api-key={nytimes_api_key}&begin_date=20230101&end_date=20231231"
# response = requests.get(search_url)
# status_code = response.status_code
# print(status_code)
# docs = response.json()["response"]["docs"]
# print(len(docs))
# for doc in docs:
#     print(doc["web_url"])


# start_date = datetime(2023, 1, 1)
# end_date = datetime(2023, 12, 31)
# papers = NyTimesScraper.get_papers_by_author_by_interval("Beth Noveck",
#                                                          "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
#                                                          start_date, end_date)
# for paper in papers:
#     print(paper)

# NyTimesScraper.test_get_papers()