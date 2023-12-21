import networkx as ntx
import pandas as pd
import matplotlib.pyplot as plt
from pyvis.network import Network

faculty = "EAI Faculty"
people = {
    "Angela Kilby": "(Core faculty) Angela Kilby is an assistant professor of economics in the College "
                     "of Social Sciences and Humanities. As a health economist, she studies the health and "
                     "welfare effects of health care policies, focusing on pain treatment and policies "
                     "to alleviate the opioid crisis.",
    "Byron Wallace": "(Affiliate faculty) Byron Wallace is an associate professor in the Khoury College of Computer "
                      "Science and director of the undergraduate program in data science. His research centers "
                      "around natural language processing and machine learning, with an emphasis "
                      "on applications in health.",
    "Dagmar Sternard": "(Affiliate faculty) Dagmar Sternad is a University Distinguished Professor in the Electrical and "
                        "Computer Engineering, Biology, and Physics departments. Her computational neuroscience "
                        "and motor control research explores the learning and control of sensorimotor "
                        "coordination in both healthy and neurologically impaired individuals.",
    "Jennifer Dy": "(Core faculty) Jennifer G. Dy is the Director of AI Faculty at the Institute for "
                    "Experiential AI. She is a professor at the Department of Electrical and Computer Engineering, "
                    "Northeastern University, Boston, MA, where she first joined the faculty in 2002."
}

industries = [
    "Banking",
    "Retail",
    "Telco",
    "Manufacturing",
    "Renewables",
    "Healthcare",
    "Life Sciences",
    "Information Technologies"
]

source = []
target = []
relationships = []
color = []
title = []
for name, desc in people.items():
    source.append(faculty)
    target.append(name)
    relationships.append("employs")
    color.append("purple")
    title.append(desc)

for industry in industries:
    source.append("Industry")
    target.append(industry)
    relationships.append("is a")
    color.append("orange")
    title.append("")

banking_use_cases = {
    "Churn Management": "",
    "Best Next Action": "",
    "Best Next Product": "",
    "Personalized Pricing": "",
    "Marketing Spend Allocation": "",
    "New Customer Acquisition": "",
    "Branch Optimization": "",
    "Credit Risk Analytics": "",
    "Fraud Analytics": "",
    "Cybersecurity": "",
    "Anti money laundering": "",
    "Cash Management": "",
    "Predictive Maintenance": "",
    "ATM/Branch Location Prediction": "",
    "Knowledge Management": "",
    "HR Analytics": "",
    "AIOps": ""
}

for use_case_name, description in banking_use_cases.items():
    source.append("Banking")
    target.append(use_case_name)
    relationships.append("has the AI use case")
    color.append("green")
    title.append(description)

healthcare_use_cases = {
    "Medical Imaging": "The goal of medical imaging with AI is to diagnose the diseases by "
                       "machine processing of medical image data",
    "Precision Medicine": "Precision medicine refers to customizing the various aspects of a treatment to the most "
                          "appropriate segment of patients with the idealization that each "
                          "segment consists of only a single patient",
    "Clinical Trials": "Using Knowledge Graph technologies, public ontologies in bio-medical domain, large language "
                       "models and NLP algorithms, critical knowledge could be "
                       "extracted from unstructured clinical trials data.",
    "Regulatory Compliance": "NLP pipelines combined with a Knowledge Graph and large language models could be used "
                             "to build an AI system for extracting the necessary data items from "
                             "company documentation and regulatory documentation to speed up the compliance process",
    "Predictive Diagnosis": "Predictive Diagnosis is building, updating and using AI models in collecting, "
                            "consolidating, cleaning, engineering the above sources "
                            "of data to provide diagnosis for various diseases",
    "Pandemic Prediction": "",
    "Social Determinants of Health": "",
    "Conversational AI": "",
    "In-house care": "",
    "Occupational Health and Safety": "",
    "AI for Pharmacovigilance": "",
    "Medical Claims Processing": "",
    "Automating Prior Authorization": "",
    "Emergency Visits": "Using a predictive model to classify patients into severity categories would benefit "
                        "who would be admitted to emergency department and "
                        "who would be directed to primary clinical care. ",
    "Healthcare Supply Chain": "",
    "Healthcare Procurement": "",
    "Patient Service Analytics": "",
    "Clinical Lab Testing": "",
    "Virtual Medical Assistants": "",
    "Question Answering": "",
    "Demand Forecasting": "",
    "Hospital Admission": "",
    "Wearable AI": "",
    "Data Quality and Integration": ""
}
for use_case_name, description in healthcare_use_cases.items():
    source.append("Healthcare")
    target.append(use_case_name)
    relationships.append("has the AI use case")
    color.append("green")
    title.append(description)

people_use_cases = {
    "Angela Kilby": (["Healthcare"], ["Precision Medicine"]),
    "Byron Wallace": (["Healthcare"], ["Precision Medicine", "Medical Imaging"]),
    "Dagmar Sternard": (["Healthcare"], ["Precision Medicine", "Medical Imaging"])
}
for person, tpl in people_use_cases.items():
    for item in tpl[0]:
        source.append(person)
        target.append(item)
        relationships.append("has research related to the industry")
        color.append("red")
        title.append("")
    for item in tpl[1]:
        source.append(person)
        target.append(item)
        relationships.append("has research related to use case")
        color.append("red")
        title.append("")


kgf = pd.DataFrame({'source': source, 'target': target, 'color': color, 'edge': relationships, 'title':title})
graph = ntx.from_pandas_edgelist(kgf, "source", "target", edge_attr=["title", "color"], create_using=ntx.MultiDiGraph())
#pos = ntx.kamada_kawai_layout(graph)
# plt.figure(figsize=(14, 14))
# posn = ntx.spring_layout(graph)
# ntx.draw(graph, with_labels=True, node_color='green', edge_cmap=plt.cm.Blues, pos=posn)
# ntx.draw_planar(graph, with_labels=True)
# plt.show()

nt = Network(height='750px', directed=True, select_menu=True, filter_menu=True, neighborhood_highlight=True)
nt.from_nx(graph)

for node in nt.nodes:
    if node["id"] == "EAI Faculty":
        node["color"] = "purple"
        node["size"] = 20
    elif node["id"] == "Industry":
        node["color"] = "red"
        node["size"] = 20
    elif node["id"] in industries:
        node["color"] = "blue"
        node["size"] = 20

nt.show('ai_graph.html', notebook=False)
nt.save_graph(r"C:\Users\omara\OneDrive\Desktop\ai_graph.html")



# nt = Network("500px", "500px")
# nt.add_node(0, label="Node 0")
# nt.add_node(1, label="Node 1", color="blue", title="Descriptive text")
# nt.add_edge(0, 1, value=4, title="Hello", from=0)
# nt.show('ai_graph.html', notebook=False)