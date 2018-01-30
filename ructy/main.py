import sys
import time
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
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

QUERY_UNIS_TITLES_TMP = """
ruct/listaestudiosuniversidad?
actual=universidades&
codigoUniversidad={}&
d-1335801-p={}
"""

KEY_CREDIT_MAP = {"Nº Créditos de Formación Básica": "CRFB",
                  "Nº Créditos Obligatorios": "CROB",
                  "Nº Créditos Optativos": "CROP",
                  "Nº Créditos en Prácticas Externas": "CREX",
                  "Nº Créditos Trabajo Fin de Grado/Master": "CRTFG"}


geolocator = GoogleV3(api_key=sys.argv[1])


# TODO create a scrapper object instead of funcions
# TODO change print to logging module

def get_url(query):
    if query[0] is not "/":
        query = "/" + query
    return "".join([BASE_URL, query])


def get_universities_page_url(page):
    return get_url(QUERY_TMP.replace("\n", "").format(page))


def get_titles_page_url(uni_id, page):
    return get_url(QUERY_UNIS_TITLES_TMP.replace("\n", "").format(uni_id, page))


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
                # TODO improve None results, i. e. not found addresses.
                proposed_address = " ".join([name,
                                             data_dict["Domicilio"].format("s/n", "").format("C/", "")
                                             ])
                location = geolocator.geocode(proposed_address)
                value = {"Dirección": location.address,
                         "Latitud": location.latitude,
                         "Longitud": location.longitude}

                # TODO check if API queries complience can stand without this time.sleep due to title scrapping
                time.sleep(0.01)
            else:
                value = span_val.contents[0]
        except Exception as e:
            print(e, key, data_dict["Código de la universidad"])

        data_dict[key] = value

    return {"Datos": data_dict}


def parse_uniersity_centers(centres_url):
    abs_url = get_url(centres_url)
    # print(abs_url)
    # TODO extract info from centers for given university
    return {"Centros": {"URL": abs_url}}


def parse_titles_data(title_url):
    abs_url = get_url(title_url)
    data_dict = {"URL": abs_url}

    response = requests.get(abs_url, verify=False)
    html = BeautifulSoup(response.content, "lxml")

    # First table 'Descripción'
    tone = html.find("div", {"id": "tone"})

    if tone:
        for label in tone.findAll("label"):
            span_key, span_val = label.findAll("span")

            key = span_key.contents[0]
            key = key.replace(":", "")

            key = KEY_CREDIT_MAP[key] if "Nº" in key else key
            key = "Código" if key == "Código del título" else key

            key = key.replace("\r", "").replace("\n", "").replace("  ", "")

            val_a = span_val.find("a")
            if val_a:
                data_dict["{} PDF URL".format(key)] = val_a["href"]
                value = str(val_a.contents[0])
            else:
                value = str(span_val.contents[0])

            data_dict[key] = value

    # Second table 'Fechas y Enlaces a BOE'
    ttwo = html.find("div", {"id": "ttwo"})

    if ttwo:
        dates_dict = {}
        for label in ttwo.findAll("label"):
            span_key, span_val = label.findAll("span")

            key = span_key.contents[0]
            key = key.replace(":", "")

            key = key.replace("\r", "").replace("\n", "").replace("  ", "")

            val_a = span_val.find("a")
            if val_a:
                dates_dict["{} PDF URL".format(key)] = val_a["href"]
                value = str(val_a.contents[0]).replace("BOE", "").replace(" ", "")
            else:
                value = str(span_val.contents[0])

            dates_dict[key] = value

        data_dict["Fechas"] = dates_dict

    return data_dict


def parse_titles_details(details_url):
    abs_url = get_url(details_url)
    details_dict = {"URL": abs_url}

    response = requests.get(abs_url, verify=False)
    html = BeautifulSoup(response.content, "lxml")

    basic_fieldset = html.find("fieldset")

    # print(abs_url)

    basic_dict = {}
    for label in basic_fieldset.findAll("label"):
        span_key = label.find("span")

        key = span_key.contents[0]
        key = key.replace(":", "")

        key = key.replace("\r", "").replace("\n", "").replace("  ", "")

        if "Acuerdo" in key or "Norma" in key or "Condición/Tipo de Vinculación" in key:
            _, span_val = label.findAll("span")

            val_a = span_val.find("a")
            if val_a:
                basic_dict["{} PDF URL".format(key)] = val_a["href"]
                value = str(val_a.contents[0])
            else:
                value = str(span_val.contents[0])

        else:
            val = label.find("input")
            try:
                value = str(val["value"])
            except (KeyError, TypeError):
                value = ""

        basic_dict[key] = value

    details_dict["Básicos"] = basic_dict

    return details_dict


def parse_uniersity_titles(titles_url, uni_data):
    abs_url = get_url(titles_url)
    titles_dict = {"URL": abs_url, "Lista": {}}

    response = requests.get(abs_url, verify=False)
    html = BeautifulSoup(response.content, "lxml")

    last_page = 0
    all_links = html.findAll("a")
    for a in all_links:
        if a.contents[0] == "Último":
            # print(a["href"])
            last_page = re.findall(r'p=\d+&', a["href"])[0]
            last_page = int(last_page.replace("p=", "").replace("&", ""))
            # print(last_page)

    for ii in range(last_page):
        n = ii + 1

        new_url = get_titles_page_url(uni_data['Código de la universidad'], n)

        response = requests.get(new_url, verify=False)
        html = BeautifulSoup(response.content, "lxml")
        table = html.find("table", {"id": "estudio"})

        # print(table.findAll("th"))
        headers = [header.contents[0] if header.contents else "" for header in table.findAll("th")]

        titles = [title.findAll("td") for title in table.find("tbody").findAll("tr")]

        d_page = {}

        for title in titles:
            d_title = {headers[ii]: col for ii, col in enumerate(title)}

            last_column = d_title.pop("").find("a")

            if last_column:
                d_title["Detalles"] = parse_titles_details(last_column["href"])
            else:
                d_title["Detalles"] = ""

            title_name = d_title.pop("Título", BeautifulSoup("<tr></tr>", "lxml"))
            title_a = title_name.find("a")
            d_title["Nombre"] = str(title_a.contents[0])
            # TODO extract all info from this URL
            d_title["Datos"] = parse_titles_data(title_a.get("href"))

            title_level = d_title.pop("Nivel académico", BeautifulSoup("<tr></tr>", "lxml"))
            d_title["Nivel académico"] = str(title_level.contents[0])

            title_state = d_title.pop("Estado", BeautifulSoup("<tr></tr>", "lxml"))
            d_title["Estado"] = str(title_state.contents[0]).replace("\xa0", "").replace("\n", "")
            d_title["Estado"] = d_title["Estado"].replace("\r", "").replace("\t", "").replace("  ", "")

            code_title = d_title.pop("Código", BeautifulSoup("<tr></tr>", "lxml"))
            code_title = code_title.contents[0].replace("\xa0", "")

            d_page[code_title] = d_title

        titles_dict["Lista"].update(d_page)

    return {"Títulos": titles_dict}


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

            uni_name = d_uni.pop("Universidad", BeautifulSoup("<tr></tr>", "lxml"))
            uni_a = uni_name.find("a")
            d_uni["Nombre"] = uni_a.contents[0]
            d_uni.update(parse_uniersity_data(uni_a.get("href")))

            centers = d_uni.pop("Centros", BeautifulSoup("<tr></tr>", "lxml"))
            d_uni.update(parse_uniersity_centers(centers.find("a").get("href")))

            titles = d_uni.pop("Títulos", BeautifulSoup("<tr></tr>", "lxml"))
            d_uni.update(parse_uniersity_titles(titles.find("a").get("href"), d_uni["Datos"]))

            code_uni = int(d_uni.pop("Código", BeautifulSoup("<tr></tr>", "lxml")).contents[0])
            d_page[code_uni] = d_uni

            # TODO make an export function
            with open("../db/{}.json".format(code_uni), "w", encoding='utf8') as output_file:
                json.dump(d_uni,
                          output_file,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '),
                          ensure_ascii=False
                          )

        d.update(d_page)

    return d


if __name__ == '__main__':
    d = parse_university_list()

