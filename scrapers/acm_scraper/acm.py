import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers.core import AuthorInfo
from scrapers.core import serialize, deserialize, create_folder_if_not_exists
import os
import re
import pandas as pd
import time
from pathlib import Path
import pickle



class AcmScraper():

    def __init__(self):
        pass

    @staticmethod
    def contains_year(s):
        # Search for a 4-digit number that represents a reasonable range for years
        # (e.g., from 1000 to 2999)
        pattern = r"\b(1[0-9]{3}|2[0-9]{3})\b"
        return bool(re.search(pattern, s))

    @staticmethod
    def month_to_int(month_name):
        month_dict = {
            "January": 1, "Jan": 1,
            "February": 2, "Feb": 2,
            "March": 3, "Mar": 3,
            "April": 4, "Apr": 4,
            "May": 5,
            "June": 6, "Jun": 6,
            "July": 7, "Jul": 7,
            "August": 8, "Aug": 8,
            "September": 9, "Sep": 9,
            "October": 10, "Oct": 10,
            "November": 11, "Nov": 11,
            "December": 12, "Dec": 12
        }
        return month_dict.get(month_name, None)

    @staticmethod
    def extract_month_year_pattern(text: str):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                  "October", "November", "December"]
        month_abbreviations = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                                 "Nov", "Dec"]
        all = months + month_abbreviations
        concat = "|".join(all)
        xxx = "[0-9]{4}"
        pattern = f"({concat}) ({xxx})"
        match = re.search(pattern, text)
        if match:
            extracted_date = match.group(0)
            return extracted_date
        else:
            return None

    @staticmethod
    def extract_year_pattern(text: str):
        match = re.search("[0-9]{4}", text)
        if match:
            return int(match.group(0))
        else:
            return None

    @staticmethod
    def get_number_of_hits(name: str, surname: str):
        url = f"https://dl.acm.org/action/doSearch?AllField=%22{name}+{surname}%22&expand=all"
        response = requests.get(url)
        hits = 0
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            hits = int(soup.find("span", {"class": "hitsLength"}).text.strip())
        return hits

    @staticmethod
    def get_papers_by_author(full_name: str, eai_url: str):
        """
        This method returns a dictionary where the keys are the authors and the values are the papers they have written.
        :param year:
        :return:
        """
        name = full_name.split(" ")[0].strip()
        surname = full_name.split(" ")[-1].strip()

        hits = AcmScraper.get_number_of_hits(name, surname)
        number_of_pages = hits // 20
        remainder = hits % 20
        if remainder > 0:
            number_of_pages += 1

        print(f"Number of items in ACM for {full_name}: {hits}")
        output = []
        count_valid = 0
        count_no_link = 0
        count_no_year = 0
        for i in range(number_of_pages):
            url = f"https://dl.acm.org/action/doSearch?AllField=%22{name}+{surname}%22&expand=all&pageSize=20&startPage={i}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                container = soup.find_all("li", {"class": "search__item issue-item-container"})
                for item in container:
                    info = AuthorInfo(full_name, eai_url)
                    info.data_source = "ACM"
                    title_block = item.find("span", {"class": ["hlFld-Title", "hlFld-ContentGroupTitle"]})
                    if title_block is not None:
                        info.title = title_block.text.strip()
                    heading = item.find("span", {"class": "issue-item__heading"})
                    if heading is not None:
                        info.type = heading.text.strip()
                    item_detail = item.find("div", {"class": "issue-item__detail"})
                    if item_detail is not None:
                        r0 = item_detail.find_all('a')
                        if len(r0) > 0:
                            info.publication = r0[0].get('title')
                        r1 = item_detail.find("a", {"class": "issue-item__doi dot-separator"})
                        if r1 is not None:
                            info.link = r1.get('href')
                        else:
                            info.link = None

                    item_title_block_01 = item.find("h5", {"class": "issue-item__title"})
                    if item_title_block_01 is not None:
                        item_title_block_02 = item_title_block_01.find("a")
                        if item_title_block_02 is not None:
                            info.link = f"https://dl.acm.org{item_title_block_02.get('href')}"
                            info.title = item_title_block_02.text.strip()

                    # date_detail = item.find("span", {"class": "dot-separator"})
                    # if date_detail is not None:
                    #     date_text = date_detail.text.strip()
                    #     extracted_date = AcmScraper.extract_month_year_pattern(date_text)
                    #     if extracted_date is not None:
                    #         year = AcmScraper.extract_year_pattern(extracted_date)
                    #         info.publication_date = datetime(year, 1, 1)
                    #     else:
                    #         info.publication_date = None

                    date_detail = item.find("div", {"class": "bookPubDate simple-tooltip__block--b"})
                    if date_detail is not None:
                        date_text = date_detail.text.strip()
                        extracted_date = AcmScraper.extract_month_year_pattern(date_text)
                        if extracted_date is not None:
                            year = int(extracted_date.split(" ")[1])
                            month = AcmScraper.month_to_int(extracted_date.split(" ")[0])
                            info.publication_date = datetime(year, month, 1)
                        else:
                            info.publication_date = None


                    if info.link is None:
                        count_no_link += 1
                        continue
                    if info.publication_date is None:
                        count_no_year += 1
                        continue
                    count_valid += 1
                    output.append(info)
            else:
               print(f"Error: {response.status_code}")
        # print(f"Valid: {count_valid}")
        # print(f"No link: {count_no_link}")
        # print(f"No year: {count_no_year}")
        return output

    @staticmethod
    def get_papers_by_author_by_interval(full_name: str, eai_url: str, start_date: datetime, end_date: datetime):
        output = AcmScraper.get_papers_by_author(full_name, eai_url)
        start_year = start_date.year
        end_year = end_date.year
        result = []
        for info in output:
            if start_year <= info.publication_date.year <= end_year:
                result.append(info)
        return result

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
                papers_by_author = AcmScraper.get_papers_by_author_by_interval(full_name, eai_url, start_date, end_date)
                print(f"Processed {pair[0]}. Number of articles: {len(papers_by_author)}")
                papers.extend(papers_by_author)
                time.sleep(60)
                # count += 1
                # if count >= 2:
                #     break
            except Exception as e:
                print(f"Error processing {pair[0]}:")
                print(e)
                time.sleep(120)

        script_path = Path(__file__).resolve()
        base_dir = script_path.parent.parent
        pkl_folder = os.path.join(base_dir, target_folder)
        create_folder_if_not_exists(pkl_folder)
        serialize(papers, os.path.join(pkl_folder, 'acm.pkl'))

    @staticmethod
    def test_get_papers():
        faculty_file = r"C:\Users\omara\OneDrive\Desktop\portal\Reservoir\iadss\NorthEastern\scraping\eai_faculty.csv"
        data = pd.read_csv(faculty_file, delimiter=",", encoding="utf-8")
        author_names_and_urls = []
        for index, row in data.iterrows():
            author_names_and_urls.append((row["Name"], row["Url"]))
        AcmScraper.get_papers(author_names_and_urls, datetime(2023, 1, 1), datetime(2023, 12, 31), "pkl_files")

    @staticmethod
    def test_get_papers_per_author(author_name: str):
        lst = AcmScraper.get_papers_by_author(author_name, " ")
        for item in lst:
            print(item.to_string())

#AcmScraper.test_get_papers()
#AcmScraper.test_get_papers_per_author("Jennifer Dy")

