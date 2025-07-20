import requests
from bs4 import BeautifulSoup

def obter_cotacao_libra_brl():
    url = "https://wise.com/br/currency-converter/gbp-to-brl-rate"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    input_element = soup.find("input", {"id": "target-input"})
    if input_element and input_element.has_attr("value"):
        valor_str = input_element["value"]
        valor_float = float(valor_str.replace(".", "").replace(",", "."))
        return valor_float/1000
    else:
        raise ValueError("Cotação não encontrada no input 'target-input'.")

if __name__ == "__main__":
    print(f"{obter_cotacao_libra_brl():.2f}")
