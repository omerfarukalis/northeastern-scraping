import urllib.request as libreq
import urllib
import requests
import feedparser
import pandas as pd
import time
from datetime import datetime
from scrapers.core import AuthorInfo
from scrapers.core import serialize, deserialize, create_folder_if_not_exists

from pathlib import Path
import pickle
import os
import time


class DblpScraper:
    @staticmethod
    def access_author():
        #url = "https://dblp.org/search/author/api/query?q=jennifer+dy&format=json&h=1"
        url = "https://dblp.org/search/author/api/query?q=usama+fayyad&format=json&h=1"
        data = urllib.request.urlopen(url)
        print(data.read().decode('utf-8'))
        # d = feedparser.parse(response_search.content.decode('utf-8'))
        # #print(d.entries[0])
        # print(response_search.content.decode('utf-8'))

    @staticmethod
    def access_publications():
        url = r"https://dblp.org/search/publ/api/query?q=usama+fayyad&format=json&h=1"
        data = urllib.request.urlopen(url)
        print(data.read().decode('utf-8'))
        # d = feedparser.parse(response_search.content.decode('utf-8'))
        # #print(d.entries[0])
        # print(response_search.content.decode('utf-8'))


    @staticmethod
    def get_affiliation(full_name:str):
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()
        reconstructed_full_name = f"{name}+{surname}"
        search_url = f"https://dblp.org/search/author/api/query?q={reconstructed_full_name}&format=json&h=1000"

        counter = 1
        output = {}
        max_results = 1000
        response = requests.get(search_url)
        status_code = response.status_code
        aff = None
        if status_code == 200:
            data = response.json()
            if len(data) == 0:
                return aff
            if "result" not in data:
                return aff
            if "hits" not in data["result"]:
                return aff
            if "hit" not in data["result"]["hits"]:
                return aff

            arr = data["result"]["hits"]["hit"]
            for item in arr:
                if "info" not in item:
                    continue
                if "notes" not in item["info"]:
                    continue
                if "note" not in item["info"]["notes"]:
                    continue
                if "@type" not in item["info"]["notes"]["note"]:
                    continue
                if item["info"]["notes"]["note"]["@type"] == "affiliation":
                    if "text" in item["info"]["notes"]["note"]:
                        aff = item["info"]["notes"]["note"]["text"]
                        break
        elif counter < 5:
            time.sleep(10)
            counter += 1
        return aff

    @staticmethod
    def get_papers_by_author_by_interval(full_name: str, eai_url: str, start_date: datetime, end_date: datetime):
        """
        Retrieve author information given the name
        :param full_name:
        :param eai_url:
        :return:
        """
        start_year = start_date.year
        end_year = end_date.year
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()
        reconstructed_full_name = f"{name}+{surname}"
        search_url = f"https://dblp.org/search/publ/api/query?q={reconstructed_full_name}&format=json&h=1000"

        affiliation = DblpScraper.get_affiliation(full_name)

        counter = 1
        output = []
        response = requests.get(search_url)
        status_code = response.status_code
        if status_code == 200:
            data = response.json()
            if len(data) == 0:
                return output
            if "result" not in data:
                return output
            if "hits" not in data["result"]:
                return output
            if "hit" not in data["result"]["hits"]:
                return output

            arr = data["result"]["hits"]["hit"]
            for item in arr:
                if "info" not in item:
                    continue
                if "year" not in item["info"]:
                    continue
                yr = int(item["info"]["year"])
                if yr < start_year or yr > end_year:
                    continue

                author = AuthorInfo(full_name, eai_url)
                if affiliation is not None:
                    author.affiliation = affiliation
                    if "northeastern" in affiliation.lower():
                        author.eai_match = True
                else:
                    author.affiliation = ""
                author.data_source = "dblp"
                author.publication_date = datetime(yr, 1, 1)
                if "url" in item["info"]:
                    author.link = item["info"]["url"]
                if "published" in item["info"]:
                    author.publication_date = datetime.strptime(item["info"]["published"], '%Y-%m-%d')
                if "type" in item["info"]:
                    if "/journals/" in author.link:
                        author.type = "journal"
                    elif "/conf/" in author.link:
                        author.type = "conference"
                    else:
                        author.type = ""
                if "venue" in item["info"]:
                    author.publication = item["info"]["venue"]

                output.append(author)

                # if author.link not in output:
                #     output[author.link] = author
        elif counter < 5:
            time.sleep(60)
            counter += 1
        return output

    @staticmethod
    def test_get_papers_by_author():
        papers = DblpScraper.get_papers_by_author_by_interval("Jennifer G. Dy",
                                                              "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
                                                              datetime(2023, 1, 1), datetime(2023, 12, 31))
        for paper in papers.values():
            print(f"{paper.full_name}, {paper.link}, {paper.type}, {paper.publication}")

    @staticmethod
    def get_papers_by_authors_by_interval(author_full_name_list: [], start_date: datetime, end_date: datetime):
        """Returns a list of papers for a given list of authors and a given time period"""
        output = []
        cnt = 0
        for pair in author_full_name_list:
            print(f"Processing the author {pair[0]}")
            full_name = pair[0]
            eai_url = pair[1]
            parsed = full_name.split(" ")
            if len(parsed) <= 1:
                continue
            name = full_name.split(" ")[0].strip()
            surname = full_name.split(" ")[-1].strip()
            papers = DblpScraper.get_author_info(name, surname, eai_url)
            output.extend(papers)
        return output

    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        DblpScraper.get_papers(author_names_and_urls, datetime(2023, 11, 1), datetime(2023, 12, 31), "pkl_files")

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
                papers_by_author = DblpScraper.get_papers_by_author_by_interval(full_name, eai_url, start_date, end_date)
                print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
                papers.extend(papers_by_author)
                time.sleep(5)
                # count += 1
                # if count >= 2:
                #     break
            except Exception as e:
                print(f"Error processing {pair[0]}:")
                print(e)
                time.sleep(120)

        for paper in papers:
            title = paper.title.replace("\n", "").replace("\t", "")
            print(f"{paper.full_name};{paper.title};{paper.data_source};{paper.type};{paper.link}")

        script_path = Path(__file__).resolve()
        base_dir = script_path.parent.parent
        pkl_folder = os.path.join(base_dir, target_folder)
        create_folder_if_not_exists(pkl_folder)
        serialize(papers, os.path.join(pkl_folder, 'dblp.pkl'))

    @staticmethod
    def test_get_papers_by_author():
        papers = DblpScraper.get_papers_by_author_by_interval("Jennifer G. Dy", "https://ai.northeastern.edu/ai-our-people/jennifer-dy/",
                                                               datetime(2023, 1, 1), datetime(2023, 12, 31))
        print(len(papers))

    @staticmethod
    def get_venue_info(venue: str):
        """
        Retrieve author information given the name
        :param first_name:
        :param last_name:
        :param eai_url:
        :return:
        """
        counter = 1
        output = {}
        max_results = 1000
        full_name = f"{first_name} {last_name}"
        parsed_name = full_name.replace(" ", "+")
        search_url = f"https://dblp.org/search/author/api/query?q={parsed_name}&format=json&h=1000"
        response = requests.get(search_url)
        status_code = response.status_code
        if status_code == 200:
            data = response.json()
            if len(data) != 0:
                arr = data["result"]["hits"]["hit"]
                for item in arr:
                    author = AuthorInfo(first_name, last_name, eai_url)
                    author.link = item["info"]["url"]
                    author.publication_date = datetime.strptime(item["info"]["published"], '%Y-%m-%d')
                    author.source = "dblp"
                    author.title = item["info"]["title"]
                    author.eai_match = False
                    if author.link not in output:
                        output[author.link] = author
        elif counter < 5:
            time.sleep(60)
            counter += 1
        return output


#DblpScraper.access_author()
#DblpScraper.access_publications()
#DblpScraper.access_publications()
#print(DblpScraper.get_affiliation("Usama Fayyad"))#DblpScraper.test_get_papers_by_author()
#DblpScraper.test_get_papers()

# start_date = datetime(2023, 1, 1)
# end_date = datetime(2023, 12, 31)
# papers_by_author = DblpScraper.get_papers_by_author_by_interval("Usama Fayyad", "", start_date, end_date)
# print(len(papers_by_author))
