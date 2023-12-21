import datetime
from typing import List
import pickle
import os
import requests
import PyPDF2
import io

class AuthorInfo:
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

    def __init__(self, full_name:str, eai_url: str):
        self.full_name = full_name
        self.eai_url = eai_url
        self.link = ""
        self.pdf_link = ""
        self.publication_date = None
        self.data_source = ""
        self.publication = ""
        self.title = ""
        self.eai_match = False
        self.affiliation = ""
        self.type = ""
        self.citations= 0

    def __str__(self):
        s = ""
        s += f"{self.full_name}, "
        s += f"{self.eai_url}, "
        s += f"{self.link}, "
        s += f"{self.pdf_link}, "
        s += f"{self.publication_date}, "
        s += f"{self.data_source}, "
        s += f"{self.publication}, "
        s += f"{self.title}, "
        s += f"{self.eai_match}, "
        s += f"{self.affiliation},"
        if self.affiliation is not None:
            s += f"{self.affiliation},"
        else:
            s += ","
        s += f"{self.type},"
        s += f"{self.citations}"
        return s

    def to_string(self):
        s = ""
        s += f"{self.full_name}\t"
        s += f"{self.eai_url}\t"
        s += f"{self.link}\t"
        s += f"{self.pdf_link}\t"
        s += f"{self.publication_date}\t"
        s += f"{self.data_source}\t"
        s += f"{self.publication}\t"
        s += f"{self.title}\t"
        s += f"{self.eai_match}\t"
        if self.affiliation is not None:
            s += f"{self.affiliation}\t"
        else:
            s += "\t"
        s += f"{self.type}\t"
        s += f"{self.citations}"
        return s


def serialize(data: List[AuthorInfo], output_file_name: str):
    with open(output_file_name, 'wb') as file:
            pickle.dump(data, file)

def deserialize(input_file_name: str):
    deserialized_obj = None
    with open(filename, 'rb') as file:
        deserialized_obj = pickle.load(file)
    return deserialized_obj

def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def validate_affiliation(pdf_url_path: str, affiliation: str):
    response = requests.get(pdf_url_path)
    if response.status_code == 200:
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        page = reader.pages[0]
        text = page.extract_text()
        if affiliation.upper() in text.upper():
            return True
    return False

#print(validate_affiliation("https://arxiv.org/pdf/2305.00380v1.pdf", "NORTHEASTERN UNIVERSITY"))
#print(validate_affiliation("https://arxiv.org/pdf/2311.00858.pdf", "NORTHEASTERN UNIVERSITY"))

