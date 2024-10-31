from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import requests
import csv

# Usamos selenium para abrir la página porque tiene un popup de privacidad
driver = webdriver.Chrome() 
web = "https://www.filmaffinity.com/es/ranking.php?rn=ranking_2024_topmovies"
driver.get(web)

time.sleep(4)

# Pulsamos el botón correspondiente a "No aceptar" el popup de privacidad
try:
    p_button = driver.find_element(By.CSS_SELECTOR, '.css-xlut8b')
    p_button.click()
    print("Privacy popup closed.")
except:
    print("Privacy popup not found.")

# Sólo se muestran los primeros 30 resultados, hay que volver a usar el webdriver de 
# Selenium para cargar más resultados hasta que salgan las 100 películas 
movie_links = []
while len(movie_links) < 100:
    movie_links = []
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #time.sleep(2)
    try:
        moreResults_button = driver.find_element(By.CSS_SELECTOR, '.show-more')
        ActionChains(driver).move_to_element(moreResults_button).click(moreResults_button).perform()
        time.sleep(2)
    except:
        print("No more results.")
    
    # Extraemos los links de los resultados de la películas
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for link in soup.select('.mc-title a'):
        if len(movie_links) < 100:
            movie_links.append(link.get('href'))
        else:
            break

# Cerrar el navegador
driver.quit()

# Definir una lista para almacenar los datos de las películas
movies_data = []

# Extraemos los datos de las 100 películas usando requests porque no tienen ningún elemento complicado
# y el popup de privacidad ya ha sido aceptado
for i, movie_link in enumerate(movie_links, 1):
    response = requests.get(movie_link)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    pos = i
    tit = soup.select_one('#main-title > span:nth-child(1)').get_text(strip=True)
    dur = soup.find("dt", string="Duración").find_next("dd").get_text(strip=True)
    pais = soup.find("dt", string="País").find_next("dd").get_text(strip=True)
    direc = soup.find("dt", string="Dirección").find_next("dd").get_text(strip=True)
    gen = soup.find("dt", string="Género").find_next("dd").get_text(strip=True)
    nota = soup.select_one('#movie-rat-avg').get_text(strip=True)
    
    movies_data.append([pos,tit, dur, pais, direc, gen, nota])

# Guardamos los datos en un archivo CSV
with open("filmaffinity_movies1.csv", mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Posición","Título", "Duración", "País", "Dirección", "Género", "Nota"])
    writer.writerows(movies_data)