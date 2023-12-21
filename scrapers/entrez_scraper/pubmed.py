import time
from typing import List
import metapub.config
from metapub import PubMedFetcher
import pickle
import os
import pandas as pd
from pathlib import Path
from core import PubMedInfo
from core import Author
import json


def are_equal_names(author, first_name, last_name):
    name = f"{first_name} {last_name}"
    if author.lower() == name.lower():
        return True
    name = f"{first_name[0]} {last_name}"
    if author.lower() == name.lower():
        return True
    name = f"{last_name[0]} {first_name}"
    if author.lower() == name.lower():
        return True
    return False


def get_pubmed_info_2(query: str):
    fetch = PubMedFetcher()
    pmids = fetch.pmids_for_query(query, retmax=10000)
    print(f"Number of articles: {len(pmids)}")
    start = time.perf_counter()
    coll = []
    cnt = 0
    for pmid in pmids:
        cnt += 1
        if cnt % 25 == 0:
            print(f"Processed {cnt}")
        try:
            pmed_out = fetch.article_by_pmid(pmid)
            mesh_terms = []
            if pmed_out.mesh is not None:
                for k, v in pmed_out.mesh.items():
                    mesh_terms.append(v["descriptor_name"])
            substances = []
            for k, v in pmed_out.chemicals.items():
                substances.append(v["substance_name"])
            auths = []
            for auth in pmed_out.author_list:
                a = Author()
                a.first_name = auth.fore_name
                a.last_name = auth.last_name
                a.name = f"{auth.fore_name} {auth.last_name}"
                a.affiliations = auth.affiliations
                auths.append(a)
            info = PubMedInfo(pmid)
            info.title = pmed_out.title
            info.abstract = pmed_out.abstract
            info.year = pmed_out.year
            info.mesh_terms = mesh_terms
            info.substances = substances
            info.authors = auths
            coll.append(info)
        except:
            print(f"Error: {pmid}")
    if len(coll) > 0:
        file_name = os.path.join(r"C:\Users\omara\OneDrive\Desktop\caf", f"caf.pkl")
        with open(file_name, 'wb') as out_file:
            pickle.dump(coll, out_file)
        end = time.perf_counter()
        print(f"Processed in {end - start} seconds")


def get_pubmed_info(authors: List[str]):
    metapub.config.API_KEY = "1fedf09fa45c6d9dbcfd3b22198a77102109"
    print(metapub.config.API_KEY)

    path = r"C:\Users\omara\OneDrive\Desktop\vip"
    dir_list = os.listdir(path)

    print("Files and directories in '", path, "' :")
    files = []
    for path in dir_list:
        files.append(Path(path).stem)

    fetch = PubMedFetcher()

    id_collected = []
    for author in authors:
        if author in files:
            print(f"{author} already computed")
            continue
        coll = []
        pmids = fetch.pmids_for_query(author, retmax=10000)
        start = time.perf_counter()
        for pmid in pmids:
            try:
                if pmid in id_collected:
                    continue
                id_collected.append(pmid)
                pmed_out = fetch.article_by_pmid(pmid)
                if pmed_out.year < 2013:
                    continue
                mesh_terms = []
                if pmed_out.mesh is not None:
                    for k, v in pmed_out.mesh.items():
                        mesh_terms.append(v["descriptor_name"])
                substances = []
                for k, v in pmed_out.chemicals.items():
                    substances.append(v["substance_name"])
                auths = []
                for auth in pmed_out.author_list:
                    a = Author()
                    a.first_name = auth.fore_name
                    a.last_name = auth.last_name
                    a.name = f"{auth.fore_name} {auth.last_name}"
                    a.affiliations = auth.affiliations
                    auths.append(a)
                info = PubMedInfo(pmid)
                info.title = pmed_out.title
                info.abstract = pmed_out.abstract
                info.year = pmed_out.year
                info.mesh_terms = mesh_terms
                info.substances = substances
                info.authors = auths
                coll.append(info)
            except:
                print(f"Error: {pmid}")

        if len(coll) > 0:
            file_name = os.path.join(r"C:\Users\omara\OneDrive\Desktop\vip", f"{author}.pkl")
            with open(file_name, 'wb') as out_file:
                pickle.dump(coll, out_file)
            end = time.perf_counter()
            print(f"Processed {pmid}  in {end - start} seconds")
    print(f"Number of articles: {len(id_collected)}")


# df = pd.read_csv(r"C:\Users\omara\OneDrive\Desktop\vip\raw\phad_clients.csv")
# lst = df["Names"].unique().tolist()
# get_pubmed_info(lst)

#get_pubmed_info_2("3d-phad or mpla OR \"monophosphoryl lipid A\"")
#get_pubmed_info_2("CAF01 or CAF09b or \"cationic adjuvant\" or \"cationic adjuvants\" or CAF09")

from scholarly import scholarly

# Retrieve the author's data, fill-in, and print
# Get an iterator for the author results
# search_query = scholarly.search_pubs("\"monophosphoryl lipid A\"")
search_query = scholarly.search_pubs("3D-PHAD")
for x in search_query:
    print(type(x))