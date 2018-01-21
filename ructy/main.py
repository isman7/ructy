import sys
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pprint
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim, GoogleV3


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://www.educacion.gob.es"

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


geolocator = GoogleV3(api_key=sys.argv[1])


def get_url(query):
    if query[0] is not "/":
        query = "/" + query
    return "".join([BASE_URL, query])


def get_universities_page_url(page):
    return get_url(QUERY_TMP.replace("\n", "").format(page))


def parse_uniersity_data(data_url):
    abs_url = get_url(data_url)
    # print(abs_url)

    data_dict = {"URL": abs_url}

    response = requests.get(abs_url, verify=False)
    html = BeautifulSoup(response.content, "lxml")
    fieldset = html.find("fieldset")
    form = html.find("div", {"id": "formulario"})
    name = form.find("h2").contents[0].contents[0]
    print(name)

    for label in fieldset.findAll("label"):
        span_key, span_val = label.findAll("span")

        key = span_key.contents[0]
        key = key.replace(" :", "")

        try:
            if key == "URL":
                value = span_val.find("a")["href"]
            elif key == "Mapa":
                proposed_address = " ".join([name,
                                             data_dict["Domicilio"].format("s/n", "").format("C/", "")
                                             ])
                location = geolocator.geocode(proposed_address)
                value = location.address
                time.sleep(0.02)
            else:
                value = span_val.contents[0]
        except Exception as e:
            print(e, key, data_dict["Código de la universidad"])

        data_dict[key] = value

    return {"Datos": data_dict}


def parse_uniersity_centers(centres_url):
    abs_url = get_url(centres_url)
    # print(abs_url)
    return {"Centros": {"URL": abs_url}}


def parse_uniersity_titles(titles_url):
    abs_url = get_url(titles_url)
    # print(abs_url)
    return {"Títulos": {"URL": abs_url}}


def parse_university_list():

    d = {}

    for n in range(9):

        i = n + 1
        ruct_url = get_universities_page_url(i)
        print(ruct_url)
        response = requests.get(ruct_url, verify=False)

        html = BeautifulSoup(response.content, "lxml")
        table = html.find("table", {"id": "universidad"})

        headers = [header.contents[0] for header in table.findAll("th")]

        universities = [uni.findAll("td") for uni in table.find("tbody").findAll("tr")]

        d_page = {}
        for uni in universities:
            d_uni = {headers[ii]: col for ii, col in enumerate(uni)}

            uni = d_uni.pop("Universidad", BeautifulSoup("<tr></tr>", "lxml"))
            uni_a = uni.find("a")
            d_uni["Nombre"] = uni_a.contents[0]
            d_uni.update(parse_uniersity_data(uni_a.get("href")))

            centers = d_uni.pop("Centros", BeautifulSoup("<tr></tr>", "lxml"))
            d_uni.update(parse_uniersity_centers(centers.find("a").get("href")))

            titles = d_uni.pop("Títulos", BeautifulSoup("<tr></tr>", "lxml"))
            d_uni.update(parse_uniersity_titles(titles.find("a").get("href")))

            code_uni = int(d_uni.pop("Código", BeautifulSoup("<tr></tr>", "lxml")).contents[0])
            d_page[code_uni] = d_uni

        d.update(d_page)

    return d


if __name__ == '__main__':
    d = parse_university_list()
    pprint.pprint(d)