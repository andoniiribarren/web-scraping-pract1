import urllib
import urllib.parse
import urllib.robotparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import csv



def movie_scraper():

    # Usamos selenium para abrir la página porque tiene un popup de privacidad

    # Configuramos las opciones para que no abra el navegador visualmente
    opts = Options()
    opts.add_argument("--headless")

    driver = webdriver.Chrome(options=opts) 
    base_url = "https://www.filmaffinity.com"
    web = f"{base_url}/es/ranking.php?rn=ranking_2024_topmovies"
    driver.get(web)

    time.sleep(3)

    # Preliminar
    user_agent = "ms"  # Movie Scraper
    robot_url = f"{base_url}/robots.txt"
    rp = urllib.robotparser.RobotFileParser(robot_url)
    # Leer el fichero robots.txt
    rp.read()
    # Obtener el delay que indica en el fichero robots
    crawl_delay = max(2, rp.crawl_delay())

    # Pulsamos el botón correspondiente a "No aceptar" el popup de privacidad
    try:
        p_button = driver.find_element(By.CSS_SELECTOR, '.css-xlut8b')
        p_button.click()
        print("Privacy popup closed.")
    except:
        print("Privacy popup not found.")

    # Sólo se muestran los primeros 30 resultados, hay que volver a usar el webdriver de 
    # Selenium para cargar más resultados hasta que salgan las 100 películas 
    
    # Usamos un set para evitar duplicados en los enlaces
    movie_links = set()
    
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
            # Exit the loop
            break
        
        # Extraemos los links de los resultados de la películas
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for link in soup.select('.mc-title a'):
            # Check with robots if we can fetch the link
            if rp.can_fetch(user_agent, link):
                if len(movie_links) < 100:
                    movie_links.append(link.get('href'))
                else:
                    break
    driver.quit()

    # Lista para almacenar los datos de las películas
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
        
        # Esperamos entre consultas para reducir la presión sobre
        # el servidor y evitar ser bloqueados
        time.sleep(crawl_delay)

    # Guardamos los datos en un archivo CSV
    with open("top100_2024films.csv", mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Posición","Título", "Duración", "País", "Dirección", "Género", "Nota"])
        writer.writerows(movies_data)


