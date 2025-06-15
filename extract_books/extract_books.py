#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import os
import re


# In[3]:


def scrape_books(pages=50):
    base_url = "http://books.toscrape.com/catalogue/page-{}.html"
    books = []
    count = 1

    for page in range(1, pages + 1):
        res = requests.get(base_url.format(page))
        if res.status_code != 200:
            print(f"Falha ao acessar a página {page}")
            continue

        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.find_all("article", class_="product_pod")

        for book in articles:
            title = book.h3.a['title']
            price_text = book.find("p", class_="price_color").text
            price = float(re.sub(r'[^\d.]', '', price_text))
            availability = book.find("p", class_="instock availability").text.strip()
            rating = book.p['class'][1]

            # Link da página individual do livro
            book_url = "http://books.toscrape.com/catalogue/" + book.h3.a['href']

            # Acessa a página de detalhes do livro
            book_res = requests.get(book_url)
            book_soup = BeautifulSoup(book_res.text, 'html.parser')

            # Categoria: está na navegação breadcrumb
            category = book_soup.select("ul.breadcrumb li a")[-1].text.strip()

            # Imagem: pega o link e ajusta para ser absoluto
            image_relative_url = book_soup.find("div", class_="item active").img['src']
            image_url = "http://books.toscrape.com/" + image_relative_url.replace('../', '')

            books.append({
                "id": count,
                "title": title,
                "Sigla_Moeda": "Libra",
                "Simbolo_Moeda": "£",
                "price": price,
                "availability": availability,
                "rating": rating,
                "category": category,
                "image_url": image_url
            })
            
            count = count+1

    df = pd.DataFrame(books)

    os.makedirs("data", exist_ok=True)
    df.to_csv('../data_base/books.csv', index=False)
    print("Dados salvos em data/books.csv")

    conn = sqlite3.connect("../data_base/books.db")
    df.to_sql("books", conn, if_exists="replace", index=False)
    conn.close()
    print("Dados salvos em data_base/books.db na tabela 'books'.")

if __name__ == "__main__":
    scrape_books()






