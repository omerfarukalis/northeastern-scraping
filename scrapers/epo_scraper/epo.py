import requests
import json
import base64
import xml.etree.ElementTree as ET
import globals
import os
import pickle
import time


class EuPatentData:
    def __init__(self):
        self.id = ""
        self.kind = ""
        self.date = ""
        self.country = ""
        self.language = ""
        self.title = ""
        self.abstract = ""
        self.applicants = []
        self.inventors = []

    def print(self):
        print(f"{self.id}, {self.date}, {self.country}, {len(self.applicants)}, {len(self.inventors)}")


class EuPatentProcessor:

    def __init__(self):
        self.key = ""
        self.secret = ""
        self.get_token_url = ""
        self.search_base_url = ""

    def search(self, query_string: str, start=0, mx=500):
        sample_string = f"{self.key}:{self.secret}"
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        base64_string = base64_bytes.decode("ascii")

        headers_token = {
            "Authorization": f"Basic {base64_string}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response_token = requests.post(self.get_token_url, headers=headers_token,
                                       data={'grant_type': 'client_credentials'})
        access_token = response_token.json()["access_token"]

        headers_get = {
            "Authorization": f"Bearer {access_token}",
            "grant_type": "client_credentials",
            "Accept": "application/exchange+xml",
            "Retry-After": "30"
        }
        lower = start+1
        upper = start+25
        counter = 0
        result = []
        while True:

            print(f"Counter {counter}")
            print(f"{lower}:{upper}")
            try:
                search_url = f"https://ops.epo.org/3.2/rest-services/published-data/search?" \
                             f"q={query_string}&Range={lower}-{upper}"
                response_search = requests.get(search_url, headers=headers_get)
                print(response_search.status_code)
                if response_search.status_code != 200:
                    break
                root = ET.fromstring(response_search.content)
                if response_search.content == "":
                    break
                if root[0][2] is None or root[0][2] == "":
                    break
                for c1 in root[0][2]:
                    patent_data = EuPatentData()
                    for c2 in c1[0]:
                        t = c2.tag.replace("{http://www.epo.org/exchange}", "")
                        if t == "abstract":
                            if c2.get("lang") == "en":
                                patent_data.language = "English"
                                patent_data.abstract = c2[0].text
                        elif t == "bibliographic-data":
                            patent_data.country = c2[0][0][0].text
                            patent_data.id = c2[0][0][1].text
                            patent_data.kind = c2[0][0][2].text
                            patent_data.date = c2[0][0][3].text
                        for c3 in c2:
                            tt = c3.tag.replace("{http://www.epo.org/exchange}", "")
                            if tt == "invention-title" and c3.get("lang") == "en":
                                patent_data.title = c3.text
                            if tt == "parties":
                                for c4 in c3:
                                    for c5 in c4:
                                        for c6 in c5:
                                            ttt = c6.tag.replace("{http://www.epo.org/exchange}", "")
                                            if ttt == "applicant-name":
                                                patent_data.applicants.append(c6[0].text)
                                            if ttt == "inventor-name":
                                                patent_data.inventors.append(c6[0].text)
                    patent_data.print()
                    result.append(patent_data)

                counter += 25

                if counter >= mx:
                    break
            except:
                print(f'Error: {lower}:{upper}')
            lower += 25
            upper += 25
        return result

    def serialize(self, result: [],  base_directory: str, output_file_name):
        if len(result) > 0:
            file_name = os.path.join(base_directory, f"{output_file_name}.pkl")
            with open(file_name, 'wb') as out_file_stream:
                pickle.dump(result, out_file_stream)


processor = EuPatentProcessor()
processor.key = globals.ep_key
processor.secret = globals.ep_secret
processor.get_token_url = "https://ops.epo.org/3.2/auth/accesstoken"
# result = processor.search("(ta = \"monophosphoryl lipid a\" OR ta = \"MPLA\" OR ta = \"3D-PHAD\") AND (ta = \"vaccine\" "
#                           "OR ta = \"vaccination\" OR ta = \"adjuvant\" OR ta = \"adjuvanted\")")

#result = processor.search("\"monophosphoryl lipid a\" OR MPLA OR 3D-PHAD")
result = processor.search("(ta=\"cationic liposome\" OR ta=\"cationic adjuvant\") and  (ta=\"vaccine\" OR ta=\"adjuvant\")")
print(len(result))

# processor.serialize(result, r"C:\Users\omara\OneDrive\Desktop\eps\mpla", "mpla_full")



#
#
# sample_string = "PuW1MzchmRM9r95aA5C0H3QcS5zjHVFZ:uQAQWwEW8u8Ie0hv"
# sample_string_bytes = sample_string.encode("ascii")
# base64_bytes = base64.b64encode(sample_string_bytes)
# base64_string = base64_bytes.decode("ascii")
# #UHVXMU16Y2htUk05cjk1YUE1QzBIM1FjUzV6akhWRlo6dVFBUVd3RVc4dThJZTBodg==
# #print(f"Encoded string: {base64_string}")
#
# api_url = "https://ops.epo.org/3.2/auth/accesstoken"
# headers = {
#     "Authorization": f"Basic {base64_string}",
#     "Content-Type": "application/x-www-form-urlencoded"
# }
# response = requests.post(api_url, headers=headers, data={'grant_type': 'client_credentials'})
# access_token = response.json()["access_token"]
#
# #get_url = "https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/EP1676595/abstract"
# get_url = "https://ops.epo.org/3.2/rest-services/published-data/search/" \
#           "biblio,abstract,?q=ta all \"Bovine herpesvirus type 1 vaccine\"&Range=5-5"
#
# headers_get = {
#     "Authorization":  f"Bearer {access_token}",
#     "grant_type": "client_credentials",
#     "Accept": "application/exchange+xml"
# }
# response_get = requests.get(get_url, headers=headers_get)
# print(response_get.status_code)
# #print(response_get.content)
#
#
#
# root = ET.fromstring(response_get.content)
# for c1 in root[0][2]:
#     for c2 in c1[0]:
#         t = c2.tag.replace("{http://www.epo.org/exchange}", "")
#         if t == "abstract":
#             lang = c2.get("lang")
#             if lang == "en":
#                 language = "English"
#                 abstract_text = c2[0].text
#         elif t == "bibliographic-data":
#             country = c2[0][0][0].text
#             number = c2[0][0][1].text
#             kind = c2[0][0][2].text
#             yyyymmdd = c2[0][0][3].text
#         for c3 in c2:
#             tt = c3.tag.replace("{http://www.epo.org/exchange}", "")
#             if tt == "invention-title" and c3.get("lang") == "en":
#                 invention_title = c3.text
#             if tt == "parties":
#                 for c4 in c3:
#                     for c5 in c4:
#                         for c6 in c5:
#                             ttt = c6.tag.replace("{http://www.epo.org/exchange}", "")
#                             if ttt == "applicant-name":
#                                 applicant_name = c6[0].text
#                             if ttt == "inventor-name":
#                                 inventor_name = c6[0].text


# for c1 in root[0][2]:
#     print(c1.tag)
#     for c2 in c1:
#         print(f"\t{c2.tag}")
#         for c3 in c2:
#             print(f"\t\t{c3.tag}")
#             for c4 in c3:
#                 print(f"\t\t\t{c4.tag}")
#                 for c5 in c4:
#                     print(f"\t\t\t\t{c5.tag}")
#                     for c6 in c5:
#                         print(f"\t\t\t\t\t{c6.tag}")

# for child in root[0][2]:
#     #print(child.tag)
#     for sub in child:
#         for sub_sub in sub:
#             print(sub_sub.tag)

# # iterate news items
# for item in root.findall('exchange-documents'):
#     news = {}
#     for child in item:
#         print(child.tag)
#         # if child.tag == '{http://search.yahoo.com/mrss/}content':
#         #     news['media'] = child.attrib['url']
#         # else:
#         #     news[child.tag] = child.text.encode('utf8')



# import xmltodict
#
# data_dict = xmltodict.parse(response_get.content)
# json_data = json.dumps(data_dict)
# print(type(json_data))


# token = epo_ops.Client.access_token
# print(token)
# client = epo_ops.Client(key='Ausra', secret='YEQ5ukf!jvj7nun.gwp')  # Instantiate client
# response = client.published_data(  # Retrieve bibliography data
#   reference_type='publication',  # publication, application, priority
#   input=epo_ops.models.Docdb('1000000', 'EP', 'A1'),  # original, docdb, epodoc
#   endpoint='biblio',  # optional, defaults to biblio in case of published_data
#   constituents=[]  # optional, list of constituents
# )
#
# print(response)


# api_url = "https://api.semanticscholar.org/graph/v1/paper/3ae0c2ef439d45a79645202f5220f3506741f8d4/" \
#           "authors?fields=affiliations,paperCount,name"
#
# headers = {
#     "Content-Type": "application/json",
#     "Accept": "application/json",
# }
# response = requests.get(api_url, headers=headers)
# print(response.status_code)
# lst = response.json()
# print(lst)