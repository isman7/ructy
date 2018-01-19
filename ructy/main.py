import requests
import pandas
from bs4 import BeautifulSoup

BASE_URL = "https://www.educacion.gob.es/{}"

QUERY_TMP = """
ruct/
listauniversidades?
tipo_univ=&
d-8320336-p={}&
cccaa=&
actual=universidades&
consulta=1&
codigoUniversidad=
"""


def get_url(query):
    return BASE_URL.format(query)


def get_universities_page_url(page):
    return get_url(QUERY_TMP.replace("\n", "").format(page))


d = []

for n in range(9):
    i = n + 1
    response = requests.get(get_universities_page_url(i), verify=False)

    html = BeautifulSoup(response.content, "lxml")
    table = html.find("table", {"id": "universidad"})

    headers = [header.contents[0] for header in table.findAll("th")]

    universities = [uni.findAll("td") for uni in table.find("tbody").findAll("tr")]

    d = d + [{headers[ii]: col for ii, col in enumerate(uni)} for uni in universities]

for col in d:
    a = col["Universidad"].find("a")
    print(a.contents[0])
    print(a['href'])

