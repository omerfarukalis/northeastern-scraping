import requests
import xml.etree.ElementTree as ET
import xmltodict
from globals import Author
from typing import Dict, List
from datetime import datetime
import os
import pickle
import spacy
import utilities

entrez_api_key = "1fedf09fa45c6d9dbcfd3b22198a77102109"
search_base_url_id = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
article_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

query_leptospira = "(leptospira[title]+OR+leptospira[abstract]+OR+leptospira[mesh]+OR+" \
                   "leptospirosis[title]+OR+leptospirosis[abstract]+OR+leptospirosis[mesh])+AND+" \
                   "(vaccine[abstract]+OR+vaccine[mesh]+OR+vaccine[title]+OR+" \
                   "adjuvant[abstract]+OR+adjuvant[mesh]+OR+adjuvant[title]+OR+" \
                   "vaccinated[abstract]+OR+vaccinated[title]+OR+" \
                   "adjuvanted[abstract]+OR+adjuvanted[title])"

query_mpla_pmc = "(\"monophosphoryl lipid a\"[abstract] or MPLA[abstract] or 3D-PHAD[abstract] or " \
                 "\"glucopyranosyl lipid a\"[abstract]) and (vaccine[abstract] or vaccine[mesh] or " \
                 "adjuvant[abstract] or adjuvant[abstract]) "

query_mpla_pubmed = "(\"monophosphoryl lipid a\"[Title/Abstract] OR MPLA[Title/Abstract] OR " \
                    " \"glucopyranosyl lipid a\"[Title/Abstract] OR \"3D-PHAD\"[Title/Abstract] OR " \
                    "\"3D-MPL\"[Title/Abstract]) AND " \
                    "(vaccine[Title/Abstract] OR adjuvant[Title/Abstract])"

query_caf_pubmed = "(CAF01 OR CAF09 OR CAF09b or \"cationic adjuvant\") AND (vaccine or adjuvant)"


url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi&api_key=1fedf09fa45c6d9dbcfd3b22198a77102109"

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&" \
      "id=9501177&api_key=1fedf09fa45c6d9dbcfd3b22198a77102109"


class EntrezInfo:

    def __init__(self, source):
        self.source = source
        self.id = {}
        self.title = ""
        self.abstract = ""
        self.body = {}
        self.authors = List[Author]
        self.keywords = List[str]
        self.date = datetime.now

    def __str__(self):
        return f"{self.source}, {self.id}"


class EntrezProcessor:

    def __init__(self, api_key, database, query, retmax, restart):
        self.api_key = api_key
        self.database = database
        self.query = query
        self.retmax = retmax
        self.restart = restart

    def get_url_id_list(self, restart: int, retmax: int):
        b = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        return f"{b}?db={self.database}&term={self.query}&retmax={retmax}" \
               f"&restart={restart}&api_key={self.api_key}"

    def get_id_list(self):
        target_url = self.get_url_id_list(self.restart, self.retmax)
        print(target_url)
        rs = self.restart
        result = []
        while True:
            response = requests.get(target_url)
            d = xmltodict.parse(response.text)
            count = int(d["eSearchResult"]["Count"])
            result.extend(d["eSearchResult"]["IdList"]["Id"])
            if len(result) >= count:
                return result
            rs += self.retmax
            target_url = self.get_url_id_list(rs, self.retmax)

    def concat_list(self, id_list: [], start: int, end: int):
        if len == 1:
            return str(int(id_list[start]))
        else:
            stmt = ""
            end_updated = min(end, len(id_list))
            for i in range(start, end_updated-1):
                stmt += f"{int(id_list[i])},"
            stmt += str(int(id_list[end_updated - 1]))
        return stmt

    def get_url_article(self, id_list: str, database: str):
        b = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        return f"{b}?db={database}&id={id_list}&api_key={self.api_key}"

    @staticmethod
    def get_date(date_info):
        year = 1
        month = 1
        day = 1
        if type(date_info) is list:
            for item in date_info:
                if "@pub-type" in item:
                    if item["@pub-type"] == "epub":
                        year = int(item["year"])
                        month = int(item["month"])
                        day = int(item["day"])
                elif "@date-type" in item:
                    if item["@date-type"] == "epub":
                        year = int(item["year"])
                        month = int(item["month"])
                        day = int(item["day"])
        else:
            if "@pub-type" in date_info:
                if date_info["@pub-type"] == "epub":
                    year = int(date_info["year"])
                    month = int(date_info["month"])
                    day = int(date_info["day"])
            elif "@date-type" in date_info:
                if date_info["@date-type"] == "epub":
                    year = int(date_info["year"])
                    month = int(date_info["month"])
                    day = int(date_info["day"])

        return datetime(year, month, day)

    @staticmethod
    def get_xref_map(lst):
        aff_by_id = {}
        if type(lst) is dict:
            if "@id" in lst and "addr-line" in lst:
                aff_by_id[lst["@id"]] = lst["addr-line"]
            elif "@id" in lst and "#text" in lst:
                aff_by_id[lst["@id"]] = lst["#text"]
        else:
            for item in lst:
                if "@id" in item and "addr-line" in item:
                    aff_by_id[item["@id"]] = item["addr-line"]
                elif "@id" in item and "#text" in item:
                    aff_by_id[item["@id"]] = item["#text"]
        return aff_by_id

    @staticmethod
    def get_author(item, xref_map):
        if type(item) is not dict:
            return None
        if "@contrib-type" in item and item["@contrib-type"] == "author":
            name = ""
            surname = ""
            full_name = ""
            if "name" in item:
                name = item["name"]["given-names"]
                surname = item["name"]["surname"]
                full_name = f"{name} {surname}"

            affiliation = ""
            if xref_map is None:
                pass
            else:
                if "xref" in item:
                    xref_list = item["xref"]
                    if type(xref_list) is list:
                        for xref in xref_list:
                            if xref["@ref-type"] == "aff":
                                if xref["@rid"] in xref_map:
                                    affiliation = xref_map[xref["@rid"]]
                    else:
                        if xref_list["@ref-type"] == "aff":
                            if xref_list["@rid"] in xref_map:
                                affiliation = xref_map[xref_list["@rid"]]

            author = Author()
            author.name = full_name
            author.first_name = name
            author.last_name = surname
            author.affiliations.append(affiliation)
            return author
        else:
            return None

    @staticmethod
    def get_authors(contrib_group, xref_map):
        author_list = []
        if type(contrib_group) is list:
            for contrib in contrib_group:
                if type(contrib["contrib"]) is list:
                    for item in contrib["contrib"]:
                        author = EntrezProcessor.get_author(item, xref_map)
                        if author is not None:
                            author_list.append(author)
                else:
                    author = EntrezProcessor.get_author(contrib["contrib"], xref_map)
                    if author is not None:
                        author_list.append(author)
        else:
            contrib = contrib_group["contrib"]
            for item in contrib:
                author = EntrezProcessor.get_author(item, xref_map)
                if author is not None:
                    author_list.append(author)
        return author_list

    @staticmethod
    def get_info(art, database: str):
        info = EntrezInfo(database)
        article_meta = art["front"]["article-meta"]
        id_array = article_meta["article-id"]
        for item in id_array:
            info.id[item["@pub-id-type"]] = item["#text"]
        info.title = article_meta["title-group"]["article-title"]

        info.abstract = ""
        if "abstract" in article_meta:
            if type(article_meta["abstract"]) is list:
                for section in article_meta["abstract"]:
                    if "p" in section:
                        if type(section["p"]) is str:
                            info.abstract += section["p"]
                        elif type(section["p"]) is dict:
                            info.abstract += section["p"]["#text"]
            else:
                if "p" in article_meta["abstract"]:
                    if type(article_meta["abstract"]["p"]) is str:
                        info.abstract += article_meta["abstract"]["p"]
                    elif type(article_meta["abstract"]["p"]) is dict:
                        info.abstract += article_meta["abstract"]["p"]["#text"]

        pub_date_info = article_meta["pub-date"]
        info.date = EntrezProcessor.get_date(pub_date_info)
        if "kwd-group" in article_meta:
            if "kwd" in article_meta["kwd-group"]:
                info.keywords = article_meta["kwd-group"]["kwd"]

        xref_map = None
        if "aff" in article_meta:
            xref_map = EntrezProcessor.get_xref_map(article_meta["aff"])
        elif "aff" in article_meta["contrib-group"]:
            xref_map = EntrezProcessor.get_xref_map(article_meta["contrib-group"]["aff"])

        author_list = EntrezProcessor.get_authors(article_meta["contrib-group"], xref_map)
        info.authors = author_list
        return info

    @staticmethod
    def get_info_pubmed_sub(data, database: str):
        info = EntrezInfo(database)
        if type(data) is not dict:
            return None
        citation = data["MedlineCitation"]

        info.id = {"pmid": citation["PMID"]["#text"]}
        #print(info.id)
        date_completed = {}
        if "DateCompleted" in citation:
            date_completed = citation["DateCompleted"]
            year = int(date_completed["Year"])
            month = int(date_completed["Month"])
            day = int(date_completed["Day"])
            info.date = datetime(year, month, day)
        elif "DateRevised" in citation:
            date_completed = citation["DateRevised"]
            year = int(date_completed["Year"])
            month = int(date_completed["Month"])
            day = int(date_completed["Day"])
            info.date = datetime(year, month, day)
        else:
            info.date = datetime(2000, 1, 1)


        art = citation["Article"]
        info.title = art["ArticleTitle"]
        if "Abstract" in art and "AbstractText" in art["Abstract"]:
            if "#text" in art["Abstract"]["AbstractText"]:
                info.abstract = art["Abstract"]["AbstractText"]["#text"]
            elif type(art["Abstract"]["AbstractText"]) is str:
                info.abstract = art["Abstract"]["AbstractText"]
            elif type(art["Abstract"]["AbstractText"]) is list:
                for item in art["Abstract"]["AbstractText"]:
                    if "#text" in item:
                        info.abstract = item["#text"]
                        break

        author_list = []
        if type(art["AuthorList"]["Author"]) is list:
            for item in art["AuthorList"]["Author"]:
                author = Author()
                if "ForeName" in item and "LastName" in item:
                    author.first_name = item["ForeName"]
                    author.last_name = item["LastName"]
                    author.name = f"{author.first_name} {author.last_name}"
                if "AffiliationInfo" in item:
                    affiliationInfo = item["AffiliationInfo"]
                    if type(affiliationInfo) is list:
                        for sub in affiliationInfo:
                            author.affiliations.append(sub["Affiliation"])
                    elif type(affiliationInfo) is dict:
                        author.affiliations.append(affiliationInfo["Affiliation"])
                    author_list.append(author)
                elif "affiliations" in item:
                    affiliationInfo = item["affiliations"]
                    if type(affiliationInfo) is list:
                        for sub in affiliationInfo:
                            author.affiliations.append(sub["Affiliation"])
                    elif type(affiliationInfo) is dict:
                        author.affiliations.append(affiliationInfo["Affiliation"])
                    author_list.append(author)
        elif type(art["AuthorList"]["Author"]) is dict:
            author = Author()
            item = art["AuthorList"]["Author"]
            if "ForeName" in item and "LastName" in item:
                author.first_name = item["ForeName"]
                author.last_name = item["LastName"]
                author.name = f"{author.first_name} {author.last_name}"
            if "AffiliationInfo" in item:
                affiliationInfo = item["AffiliationInfo"]
                if type(affiliationInfo) is list:
                    for sub in affiliationInfo:
                        author.affiliations.append(sub["Affiliation"])
                elif type(affiliationInfo) is dict:
                    author.affiliations.append(affiliationInfo["Affiliation"])
                author_list.append(author)
            elif "affiliations" in item:
                affiliationInfo = item["affiliations"]
                if type(affiliationInfo) is list:
                    for sub in affiliationInfo:
                        author.affiliations.append(sub["Affiliation"])
                elif type(affiliationInfo) is dict:
                    author.affiliations.append(affiliationInfo["Affiliation"])
                author_list.append(author)
        info.authors = author_list
        return info

    def get_info_pmc(self, id_list: [], batch_size: int, database: str):
        info_array = []
        cursor = 0
        while True:
            id_list_as_string = self.concat_list(id_list, cursor, cursor + batch_size)
            url_article = self.get_url_article(id_list_as_string, database)
            response = requests.get(url_article)
            d = xmltodict.parse(response.text)
            if type(d["pmc-articleset"]["article"]) is dict:
                art = d["pmc-articleset"]["article"]
                try:
                    info = EntrezProcessor.get_info(art, database)
                    info_array.append(info)
                except:
                    print("PMC error")

            elif type(d["pmc-articleset"]["article"]) is list:
                for art in d["pmc-articleset"]["article"]:
                    try:
                        info = EntrezProcessor.get_info(art, database)
                        info_array.append(info)
                    except:
                        print("PMC error")

            print(f"{cursor}: {len(info_array)}")
            cursor += batch_size
            if cursor >= len(id_list):
                break
        return info_array

    def get_info_pubmed(self, id_list: [], batch_size: int, database: str):
        info_array = []
        cursor = 0
        while True:
            id_list_as_string = self.concat_list(id_list, cursor, cursor + batch_size)
            url_article = self.get_url_article(id_list_as_string, database)
            response = requests.get(url_article)
            d = xmltodict.parse(response.text)
            for art in d["PubmedArticleSet"]["PubmedArticle"]:
                try:
                    info = EntrezProcessor.get_info_pubmed_sub(art, database)
                    if info is not None and len(info.abstract) >= 100:
                        info_array.append(info)
                except:
                    print("Error")
            print(f"{cursor}: {len(info_array)}")
            cursor += batch_size
            if cursor >= len(id_list):
                break
        return info_array


    @staticmethod
    def serialize(result: [], output_file_name):
        if len(result) > 0:
            with open(output_file_name, 'wb') as out_file_stream:
                pickle.dump(result, out_file_stream)

    @staticmethod
    def clean_name(name: str):
        s = ""
        for c in name:
            if c.isalpha() or c == ' ':
                s += c
        return s


    @staticmethod
    def get_pmc_mpla_articles(output_file_name: str):
        processor = EntrezProcessor(entrez_api_key, "pmc", query_mpla_pmc, 10000, 0)
        id_list = processor.get_id_list()
        print(len(id_list))
        info_array = processor.get_info_pmc(id_list, 50, "pmc")
        print(len(info_array))
        EntrezProcessor.serialize(info_array, output_file_name)

    @staticmethod
    def get_pmc_articles(query: str, output_file_name: str):
        processor = EntrezProcessor(entrez_api_key, "pmc", query, 10000, 0)
        id_list = processor.get_id_list()
        print(len(id_list))
        info_array = processor.get_info_pmc(id_list, 50, "pmc")
        print(len(info_array))
        EntrezProcessor.serialize(info_array, output_file_name)

    @staticmethod
    def get_pubmed_mpla_articles(output_file_name: str):
        processor = EntrezProcessor(entrez_api_key, "pubmed", query_mpla_pubmed, 10000, 0)
        id_list = processor.get_id_list()
        print(len(id_list))
        info_array = processor.get_info_pubmed(id_list, 50, "pubmed")
        print(len(info_array))
        EntrezProcessor.serialize(info_array, output_file_name)

    @staticmethod
    def get_pubmed_caf_articles(output_file_name: str):
        processor = EntrezProcessor(entrez_api_key, "pubmed", query_caf_pubmed, 10000, 0)
        id_list = processor.get_id_list()
        print(len(id_list))
        info_array = processor.get_info_pubmed(id_list, 50, "pubmed")
        print(len(info_array))
        EntrezProcessor.serialize(info_array, output_file_name)

    @staticmethod
    def get_pubmed_articles(query: str, output_file_name: str):
        processor = EntrezProcessor(entrez_api_key, "pubmed", query, 10000, 0)
        id_list = processor.get_id_list()
        print(len(id_list))
        info_array = processor.get_info_pubmed(id_list, 50, "pubmed")
        print(len(info_array))
        EntrezProcessor.serialize(info_array, output_file_name)

    @staticmethod
    def merge_pmc_and_pubmed(pickle_pmc_file: str, pickle_pubmed_file: str, out_file_name: str):
        pubmed_records = {}
        with open(pickle_pubmed_file, 'rb') as in_file:
            pubmed_records = pickle.load(in_file)
        pubmed_identifiers = {}
        for item in pubmed_records:
            pubmed_identifiers[item.id["pmid"]] = item
        pmc_records = []
        with open(pickle_pmc_file, 'rb') as in_file:
            pmc_records = pickle.load(in_file)

        merged = []
        for item in pmc_records:
            pubmed_id = item.id["pmid"]
            if pubmed_id not in pubmed_identifiers:
                merged.append(item)
        for item in pubmed_records:
            merged.append(item)
        print(len(merged))
        EntrezProcessor.serialize(merged, out_file_name)

    @staticmethod
    def print_author_info(pickle_file_name: str, out_file_name: str):
        collection = List[EntrezInfo]
        with open(pickle_file_name, 'rb') as in_file:
            collection = pickle.load(in_file)
        lst = []
        filtered = 0
        for info in collection:
            if info.date.year < 2013:
                filtered += 1
                continue
            year = info.date.year
            id_pubmed = ""
            id_pmc = ""
            for k, v in info.id.items():
                if k == "pmc":
                    id_pmc = v
                elif k == "pmid":
                    id_pubmed = v

            if len(info.authors) <= 25:
                for author in info.authors:
                    #author_name = EntrezProcessor.clean_name(author.name)
                    author_name = EntrezProcessor.clean_name(author.name)
                    lst.append((id_pmc, id_pubmed, year, author_name))
        print(f"Filtered: {filtered}")
        with open(out_file_name, 'w', encoding='utf-8') as out_file:
            out_file.write("PMC_Id, PubMed_Id, Year, Author\n")
            for item in lst:
                out_file.write(f"{item[0]}, {item[1]}, {item[2]}, {item[3]}\n")


    @staticmethod
    def print_author_affiliation(pickle_file_name: str, out_file_name: str):
        nlp = spacy.load("en_core_web_sm")
        output = {}
        collection = List[EntrezInfo]
        error = 0
        with open(pickle_file_name, 'rb') as in_file:
            collection = pickle.load(in_file)
            for item in collection:
                try:
                    if len(item.authors) >= 25:
                        continue
                    if int(item.date.year) < 2013:
                        continue
                    authors = item.authors
                    for author in authors:
                        affiliations = author.affiliations
                        for aff in affiliations:

                            doc = nlp(aff)
                            org = utilities.get_org(doc)
                            location = utilities.get_gpe(doc)
                            country = utilities.get_country(location)
                            # email = utilities.get_email(doc)
                            if "Belgium" in country or "Germany" in country or "Switzerland" in country or "Austria" in country or "Netherlands" in country:
                                if author.name not in output:
                                    output[author.name] = []
                                output[author.name].append((org, location, country))
                except:
                    error += 1

        print(f"Error: {error}")
        with open(out_file_name, "w", encoding="utf-8") as work_data:
            work_data.write("Name\tInstitution\tLocation\tCountry\tPublications\n")
            for key, value in output.items():
                for item in value:
                    work_data.write(f"{key}\t{item[0]}\t{item[1]}\t{item[2]}\t{len(value)}\n")

    @staticmethod
    def print_researcher_info(pickle_file_name: str, out_file_name: str):
        nlp = spacy.load("en_core_web_sm")
        output = {}
        collection = List[EntrezInfo]
        error = 0
        kwd_count = {}
        with open(pickle_file_name, 'rb') as in_file:
            collection = pickle.load(in_file)
            for item in collection:
                if len(item.authors) >= 25:
                    continue
                if int(item.date.year) < 2013:
                    continue
                authors = item.authors
                for author in authors:
                    affiliations = author.affiliations
                    for aff in affiliations:
                        doc = nlp(aff)
                        org = utilities.get_org(doc)
                        location = utilities.get_gpe(doc)
                        country = utilities.get_country(location)
                        # email = utilities.get_email(doc)
                        if "Belgium" in country or "Germany" in country or "Switzerland" in country or "Austria" in country or "Netherlands" in country:
                            if author.name not in output:
                                output[author.name] = []
                            output[author.name].append((org, country))
                mpla_count = 0
                gla_count = 0
                phad_count = 0
                if "MPLA" in item.abstract or "MPLA":
                    mpla_count += 1
                if "monophosphoryl Lipid A" in item.abstract:
                    mpla_count += 1
                if "glucopyranosyl lipid A" in item.abstract:
                    gla_count += 1
                if "PHAD" in item.abstract:
                    phad_count += 1
                if "3D-PHAD" in item.abstract:
                    phad_count += 1
                if "3D-MPL" in item.abstract:
                    phad_count += 1
                for author in authors:
                    name = author.name
                    if name not in kwd_count:
                        kwd_count[name] = [0, 0, 0]
                    kwd_count[name][0] += mpla_count
                    kwd_count[name][1] += gla_count
                    kwd_count[name][2] += phad_count

        reduced = {}
        for author_name, data in output.items():
            article_count = len(data)
            org = data[0][0]
            country = data[0][1]
            reduced[author_name] = (author_name, org, country, article_count)

        print(f"Error: {error}")
        with open(out_file_name, "w", encoding="utf-8") as work_data:
            work_data.write("Name\tAuthor\tOrganization\tCountry\tPublications\tMPLA\tGLA\tPHAD\n")
            for key, value in reduced.items():
                work_data.write(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}\t{value[3]}\t{kwd_count[key][0]}\t{kwd_count[key][1]}\t{kwd_count[key][2]}\n")

        # print(f"Error: {error}")
        # with open(out_file_name, "w", encoding="utf-8") as work_data:
        #     work_data.write("Name\tAuthor\tOrganization\tCountry\tPublications\n")
        #     for key, value in reduced.items():
        #         work_data.write(
        #             f"{key}\t{value[0]}\t{value[1]}\t{value[2]}\t{value[3]}\n")

    @staticmethod
    def print_country_info(pickle_file_name: str, out_file_name: str):
        nlp = spacy.load("en_core_web_sm")
        output = {}
        collection = List[EntrezInfo]
        error = 0
        kwd_count = {}
        with open(pickle_file_name, 'rb') as in_file:
            collection = pickle.load(in_file)
            for item in collection:
                if len(item.authors) >= 25:
                    continue
                if int(item.date.year) < 2013:
                    continue
                authors = item.authors
                for author in authors:
                    affiliations = author.affiliations
                    for aff in affiliations:
                        doc = nlp(aff)
                        org = utilities.get_org(doc)
                        location = utilities.get_gpe(doc)
                        country = utilities.get_country(location)
                        # email = utilities.get_email(doc)
                        if "Belgium" in country or "Germany" in country or "Switzerland" in country or "Austria" in country or "Netherlands" in country:
                            if author.name not in output:
                                output[author.name] = []
                            output[author.name].append((org, country))
                mpla_count = 0
                gla_count = 0
                phad_count = 0
                if "MPLA" in item.abstract or "MPLA":
                    mpla_count += 1
                if "monophosphoryl Lipid A" in item.abstract:
                    mpla_count += 1
                if "glucopyranosyl lipid A" in item.abstract:
                    gla_count += 1
                if "PHAD" in item.abstract:
                    phad_count += 1
                if "3D-PHAD" in item.abstract:
                    phad_count += 1
                if "3D-MPL" in item.abstract:
                    phad_count += 1
                for author in authors:
                    name = author.name
                    if name not in kwd_count:
                        kwd_count[name] = [0, 0, 0]
                    kwd_count[name][0] += mpla_count
                    kwd_count[name][1] += gla_count
                    kwd_count[name][2] += phad_count
        reduced = {}
        for author_name, data in output.items():
            article_count = len(data)
            org = data[0][0]
            country = data[0][1]
            if country not in reduced:
                reduced[country] = [0, 0, 0, 0, 0]
            reduced[country][0] += 1
            reduced[country][1] += article_count
            reduced[country][2] += kwd_count[author_name][0]
            reduced[country][3] += kwd_count[author_name][1]
            reduced[country][4] += kwd_count[author_name][2]

        print(f"Error: {error}")
        with open(out_file_name, "w", encoding="utf-8") as work_data:
            work_data.write("Country\tResearcher\tPublications\tMPLA\tGLA\tPHAD\n")
            for key, value in reduced.items():
                work_data.write(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}\t{value[3]}\t{value[4]}\n")

        # with open(out_file_name, "w", encoding="utf-8") as work_data:
        #     work_data.write("Country\tResearcher\tPublications\n")
        #     for key, value in reduced.items():
        #         work_data.write(f"{key}\t{value[0]}\t{value[1]}\n")

    # @staticmethod
    # def print_researcher_info_2(pickle_file_name: str, out_file_name: str):
    #     nlp = spacy.load("en_core_web_sm")
    #     output = {}
    #     collection = List[EntrezInfo]
    #     error = 0
    #     kwd_count = {}
    #     with open(pickle_file_name, 'rb') as in_file:
    #         collection = pickle.load(in_file)
    #         for item in collection:
    #             if len(item.authors) >= 25:
    #                 continue
    #             if int(item.date.year) < 2013:
    #                 continue
    #             authors = item.authors
    #             for author in authors:
    #                 affiliations = author.affiliations
    #                 for aff in affiliations:
    #                     doc = nlp(aff)
    #                     org = utilities.get_org(doc)
    #                     location = utilities.get_gpe(doc)
    #                     country = utilities.get_country(location)
    #                     # email = utilities.get_email(doc)
    #                     if "Belgium" in country or "Germany" in country or "Switzerland" in country or "Austria" in country or "Netherlands" in country:
    #                         if author.name not in output:
    #                             output[author.name] = []
    #                         output[author.name].append((org, country))
    #     reduced = {}
    #     for author_name, data in output.items():
    #         article_count = len(data)
    #         org = data[0][0]
    #         country = data[0][1]
    #         if country not in reduced:
    #             reduced[country] = [0, 0]
    #         reduced[country][0] += 1
    #         reduced[country][1] += article_count
    #
    #     print(f"Error: {error}")
    #     with open(out_file_name, "w", encoding="utf-8") as work_data:
    #         work_data.write("Country\tResearcher\tPublications\n")
    #         for key, value in reduced.items():
    #             work_data.write(f"{key}\t{value[0]}\t{value[1]}\n")

    @staticmethod
    def print_org_info(pickle_file_name: str, out_file_name: str):
        nlp = spacy.load("en_core_web_sm")
        output = {}
        collection = List[EntrezInfo]
        error = 0
        kwd_count = {}
        with open(pickle_file_name, 'rb') as in_file:
            collection = pickle.load(in_file)
            for item in collection:
                if len(item.authors) >= 25:
                    continue
                if int(item.date.year) < 2013:
                    continue
                authors = item.authors
                for author in authors:
                    affiliations = author.affiliations
                    for aff in affiliations:
                        doc = nlp(aff)
                        org = utilities.get_org(doc)
                        location = utilities.get_gpe(doc)
                        country = utilities.get_country(location)
                        # email = utilities.get_email(doc)
                        if "Belgium" in country or "Germany" in country or "Switzerland" in country or "Austria" in country or "Netherlands" in country:
                            if author.name not in output:
                                output[author.name] = []
                            output[author.name].append((org, country))
                mpla_count = 0
                gla_count = 0
                phad_count = 0
                if "MPLA" in item.abstract or "MPLA":
                    mpla_count += 1
                if "monophosphoryl Lipid A" in item.abstract:
                    mpla_count += 1
                if "glucopyranosyl lipid A" in item.abstract:
                    gla_count += 1
                if "PHAD" in item.abstract:
                    phad_count += 1
                if "3D-PHAD" in item.abstract:
                    phad_count += 1
                if "3D-MPL" in item.abstract:
                    phad_count += 1
                for author in authors:
                    name = author.name
                    if name not in kwd_count:
                        kwd_count[name] = [0, 0, 0]
                    kwd_count[name][0] += mpla_count
                    kwd_count[name][1] += gla_count
                    kwd_count[name][2] += phad_count
        reduced = {}
        for author_name, data in output.items():
            article_count = len(data)
            org = data[0][0]
            country = data[0][1]
            if org not in reduced:
                reduced[org] = ["", 0, 0, 0, 0, 0]
            reduced[org][0] = country
            reduced[org][1] += 1
            reduced[org][2] += article_count
            reduced[org][3] += kwd_count[author_name][0]
            reduced[org][4] += kwd_count[author_name][1]
            reduced[org][5] += kwd_count[author_name][2]

        with open(out_file_name, "w", encoding="utf-8") as work_data:
            work_data.write("Org\tCountry\tResearcher\tPublications\tMPLA\tGLA\tPHAD\n")
            for key, value in reduced.items():
                work_data.write(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}\t{value[3]}\t{value[4]}\t{value[5]}\n")

        # with open(out_file_name, "w", encoding="utf-8") as work_data:
        #     work_data.write("Org\tCountry\tResearcher\tPublications\n")
        #     for key, value in reduced.items():
        #         work_data.write(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}\n")


""" PMC """
file_pmc_mpla = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\data_phad_pmc.pkl"
file_pubmed_mpla = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\data_phad_pubmed.pkl"
file_merged_mpla = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\data_phad_pmc_pubmed.pkl"
#EntrezProcessor.get_pmc_mpla_articles(file_pmc_mpla)
#EntrezProcessor.get_pubmed_mpla_articles(file_pubmed_mpla)
#EntrezProcessor.merge_pmc_and_pubmed(file_pmc_mpla, file_pubmed_mpla, file_merged_mpla)

file_author_id_mpla_pubmed = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\author_id_phad_pubmed.txt"
#EntrezProcessor.print_author_info(file_pubmed_mpla, file_author_id_mpla_pubmed)

file_author_aff_mpla_pubmed = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\author_aff_phad_pubmed.txt"
#EntrezProcessor.print_author_affiliation(file_pubmed_mpla, file_author_aff_mpla_pubmed)

file_researcher_info_phad_pubmed = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\researcher_info_phad_pubmed.txt"
#EntrezProcessor.print_researcher_info(file_pubmed_mpla, file_researcher_info_phad_pubmed)

file_country_counts_mpla_pubmed = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\country_counts_phad_pubmed.txt"
#EntrezProcessor.print_country_info(file_pubmed_mpla, file_country_counts_mpla_pubmed)

file_org_mpla_pubmed = r"C:\Users\omara\OneDrive\Desktop\phad\feb18\org_info_phad_pubmed.txt"
#EntrezProcessor.print_org_info(file_pubmed_mpla, file_org_mpla_pubmed)


""" PubMed """
file_pubmed_caf = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\data_caf_pubmed.pkl"
#EntrezProcessor.get_pubmed_caf_articles(file_pubmed_caf)

file_author_id_caf_pubmed = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\author_id_caf_pubmed.txt"
#EntrezProcessor.print_author_info(file_pubmed_caf, file_author_id_caf_pubmed)

file_author_aff_caf_pubmed = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\author_aff_caf_pubmed.txt"
#EntrezProcessor.print_author_affiliation(file_pubmed_caf, file_author_aff_caf_pubmed)

file_researcher_info_caf_pubmed = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\researcher_info_caf_pubmed.txt"
#EntrezProcessor.print_researcher_info(file_pubmed_caf, file_researcher_info_caf_pubmed)

file_country_counts_caf_pubmed = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\country_stats_caf_pubmed.txt"
#EntrezProcessor.print_country_info(file_pubmed_caf, file_country_counts_caf_pubmed)

file_org_caf_pubmed = r"C:\Users\omara\OneDrive\Desktop\caf\feb18\org_info_caf_pubmed.txt"
#EntrezProcessor.print_org_info(file_pubmed_caf, file_org_caf_pubmed)





# root = ET.fromstring(response.content)
# for item in root[0][1][1]:
#     print(item.tag)
#     print(item.text)

# for c0 in root:
#     print(c0.tag)
#     print(c0.text)
#     for c1 in c0:
#         print(f"\t{c1.tag}:{c1.text}")
#         for c2 in c1:
#             print(f"\t\t{c2.tag}:{c2.text}")
#             for c3 in c2:
#                 print(f"\t\t\t{c3.tag}{c3.text}:")
#                 for c4 in c3:
#                     print(f"\t\t\t\t{c4.tag}:{c4.text}")
#                     for c5 in c4:
#                         print(f"\t\t\t\t{c5.tag}:{c5.text}")
#                         for c6 in c5:
#                             print(f"\t\t\t\t{c6.tag}:{c6.text}")
