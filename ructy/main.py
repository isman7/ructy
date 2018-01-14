import requests
import pandas

response = requests.get("https://www.educacion.gob.es/ruct/listauniversidades?tipo_univ=&d-8320336-p=6&cccaa=&actual=universidades&consulta=1&codigoUniversidad=",
             verify=False)

dataframe = pandas.read_html(response.content.decode(encoding='utf-8', errors="ignore"),
                             attrs={"id": "universidad"})

print(dataframe)
