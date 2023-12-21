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
import json
from typing import List


# def __init__(self, name: str, surname: str, eai_url: str):
#     self.name = name
#     self.surname = surname
#     self.eai_url = eai_url
#     self.full_name = f"{self.name} {self.surname}"
#     self.link = ""
#     self.pdf_link = ""
#     self.publication_date = datetime.datetime.now()
#     self.source = ""
#     self.title = ""
#     self.eai_match = False
#     self.affiliation = ""
#     self.venue = ""

# url_projects = 'https://api.reporter.nih.gov/v2/projects/search'
# url_publications = 'https://api.reporter.nih.gov/v2/publications/search'

class NihData:
    def __init__(self):
        self.org_name = ""
        self.pi_name = ""
        self.principal_investigators = []
        self.project_title = ""
        self.project_start_date = ""
        self.project_end_date = ""
        self.abstract = ""
        self.project_detail_url = ""


class NihScraper:
    @staticmethod
    def get_ne_projects() -> List[NihData]:
        url = 'https://api.reporter.nih.gov/v2/projects/search'
        offset = 0
        payload = {
            "criteria": {
                "org_names": ["NORTHEASTERN UNIVERSITY"],
                "org_cities": ["BOSTON"],
                #"pi_names": [{"any_name": "GOODWIN"}, {"any_name": "DAGMAR"}, {"any_name": "TUNIK"}]
            },
            "include_fields": [
                "ApplId", "SubprojectId", "FiscalYear", "Organization", "ProjectNum", "OrgCountry",
                "ProjectNumSplit", "ContactPiName", "AllText", "FullStudySection",
                "ProjectStartDate", "ProjectEndDate", "AbstractText", "ProjectTitle", "PrincipalInvestigators",
                "ProjectDetailUrl"
            ],
            "offset": offset,
            "limit": 500,
            "sort_field": "project_start_date",
            "sort_order": "desc"
        }
        page = 1
        output = []
        while True:
            #print(f"Page {page}")
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                results = data["results"]
                for result in results:
                    nih_data = NihData()
                    nih_data.org_name = result["organization"]["org_name"]
                    nih_data.pi_name = result["contact_pi_name"]
                    pi_list = result["principal_investigators"]
                    for pi in pi_list:
                        first_name = pi["first_name"].strip().upper()
                        last_name = pi["last_name"].strip().upper()
                        nih_data.principal_investigators.append(f"{first_name} {last_name}")
                    nih_data.project_title = result["project_title"]
                    if result["project_start_date"] is not None:
                        nih_data.project_start_date = datetime.strptime(result["project_start_date"].strip(), '%Y-%m-%dT%H:%M:%SZ')
                    else:
                        nih_data.project_start_date = None
                    if result["project_end_date"] is not None:
                        nih_data.project_end_date = datetime.strptime(result["project_end_date"].strip(), '%Y-%m-%dT%H:%M:%SZ')
                    else:
                        nih_data.project_end_date = None
                    nih_data.abstract = result["abstract_text"]
                    nih_data.project_detail_url = result["project_detail_url"]
                    output.append(nih_data)
                if len(results) < 500:
                    break
                offset += 500
                page += 1
                payload["offset"] = offset
            else:
                break
        return output

    @staticmethod
    def serialize(data: List[NihData], output_file_name: str):
        with open(output_file_name, 'wb') as file:
                pickle.dump(data, file)

    @staticmethod
    def deserialize(input_file_name: str) -> List[NihData]:
        deserialized_obj = None
        with open(input_file_name, 'rb') as file:
            deserialized_obj = pickle.load(file)
        return deserialized_obj

    @staticmethod
    def get_name_list(author_names_and_urls: []):
        names = []
        for pair in author_names_and_urls:
            full_name = pair[0]
            name = full_name.split(" ")[0].strip().upper()
            surname = full_name.split(" ")[-1].strip().upper()
            names.append((name, surname))
        return names

    # @staticmethod
    # def search_name(pi: str, name_list = List[(str, str)]):
    #     for name in name_list:
    #         if name[0] in pi.upper() and name[1] in pi.upper():
    #             return True
    #     return False

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
        print("Getting NIH projects...")
        projects = NihScraper.get_ne_projects()
        print("Serializing NIH projects...")
        script_path = Path(__file__).resolve()
        nih_scraper_folder = script_path.parent
        nih_pkl_file_path = os.path.join(nih_scraper_folder, "nih_projects.pkl")
        serialize(projects, nih_pkl_file_path)
        print("Deserializing NIH projects...")
        projects = NihScraper.deserialize(nih_pkl_file_path)
        name_list = NihScraper.get_name_list(author_names_and_urls)
        authors = []
        for project in projects:
            if project.project_start_date is None:
                continue
            if project.project_start_date < start_date:
                continue
            for pi in project.principal_investigators:
                for tpl in name_list:
                    if tpl[0] in pi.upper() and tpl[1] in pi.upper():
                        # print(f"Name: {tpl[0]} {tpl[1]}")
                        # print(f"Project:  {project.project_title}")
                        # print(f"Project start date:  {project.project_start_date}")
                        # print(f"Project end date:  {project.project_end_date}")
                        # print(pi)
                        author = AuthorInfo(pi, "")
                        author.link = project.project_detail_url
                        author.publication_date = project.project_start_date
                        author.data_source = "nih"
                        author.title = project.project_title
                        author.eai_match = True
                        author.publication = "nih"
                        author.type = "grant"
                        author.affiliation = project.org_name
                        author.venue = ""
                        authors.append(author)
        base_dir = script_path.parent.parent
        pkl_folder = os.path.join(base_dir, target_folder)
        create_folder_if_not_exists(pkl_folder)
        serialize(authors, os.path.join(pkl_folder, 'nih.pkl'))
        return authors

        #
        # papers = []
        # count = 0
        # for pair in author_names_and_urls:
        #     full_name = pair[0]
        #     eai_url = pair[1]
        #     try:
        #         papers_by_author = SemanticScholarScraper.get_papers_by_author_by_interval(full_name, eai_url,
        #                                                                                    start_date, end_date)
        #         print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
        #         papers.extend(papers_by_author)
        #         time.sleep(5)
        #         # count += 1
        #         # if count >= 2:
        #         #     break
        #     except Exception as e:
        #         print(f"Error processing {pair[0]}:")
        #         print(e)
        #         time.sleep(10)
        #
        # for paper in papers:
        #     title = paper.title.replace("\n", "").replace("\t", "")
        #     print(f"{paper.full_name};{title};{paper.data_source};{paper.type};{paper.link}")
        #
        # script_path = Path(__file__).resolve()
        # base_dir = script_path.parent.parent
        # pkl_folder = os.path.join(base_dir, target_folder)
        # create_folder_if_not_exists(pkl_folder)
        # serialize(papers, os.path.join(pkl_folder, 'semantic_scholar.pkl'))

# projects = NihScraper.get_ne_projects()
# serialize(projects, "nih_projects.pkl")

# projects = NihScraper.deserialize("nih_projects.pkl")
# print(len(projects))

# faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
# data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
# author_list = []
# for index, row in data.iterrows():
#     author_list.append((row["Name"], row["Url"]))
#
# start_date = datetime(1900, 1, 1)
# end_date = datetime(2023, 12, 31)
# target_folder = "pkl_files"
# NihScraper.get_papers(author_list, start_date, end_date, target_folder)