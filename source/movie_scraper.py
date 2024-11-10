#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# cython: language_level=3

import os
import urllib
import urllib.parse
import urllib.robotparser

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *


from bs4 import BeautifulSoup
import time
import requests
import csv

from tqdm import tqdm

USE_HEADLESS = False
DEFAULT_CRAWL_DELAY_S = 0.1

def movie_scraper():

    
    # https://www.filmaffinity.com/es/ranking.php?rn=ranking_2024_topmovies
    base_url = "https://www.filmaffinity.com"
    url_objetivo = f"{base_url}/es/ranking.php?rn=ranking_2024_topmovies"

    #
    # Preliminar
    #
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    robot_url = f"{base_url}/robots.txt"
    rp = urllib.robotparser.RobotFileParser(robot_url)
    
    # Leer el fichero robots.txt
    # Esta web rechaza la lectura realizada por defecto por la clase RobotFileParser,
    # así que leeremos el archivo con una request
    #rp.read()
    
    headers={'User-Agent':user_agent,} 
    request=urllib.request.Request(robot_url,None,headers)
    response = urllib.request.urlopen(request)
    robot_data_raw = response.read() 
    
    # Pasar el contenido a rp
    rp.parse(robot_data_raw.decode("utf-8").splitlines())
    
    
    # Obtener el delay que indica en el fichero robots
    crawl_delay = rp.crawl_delay(user_agent)
    if crawl_delay is None:
        # Establecer 1 como delay porque no hay ninguno especificado en el servidor
        crawl_delay = DEFAULT_CRAWL_DELAY_S
    else:
        # Establecer un mínimo de 1
        crawl_delay = max(DEFAULT_CRAWL_DELAY_S, crawl_delay)


    # Usamos selenium para abrir la página porque tiene un popup de privacidad
    # Configuramos las opciones para que no abra el navegador visualmente
    opts = Options()
    if USE_HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--user-agent={user_agent}")

    # Crear el driver y cargar la página
    driver = webdriver.Chrome(options=opts) 
    driver.get(url_objetivo)

    
    # Pulsamos el botón correspondiente a "No aceptar" el popup de privacidad
    try:
        # Esperamos a que aparezca el botón de popup de privacidad
        WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.css-xlut8b')))

        # Hacemos click en el botón
        p_button = driver.find_element(By.CSS_SELECTOR, '.css-xlut8b')
        p_button.click()
        print("Privacy popup closed.")
    except TimeoutException as te:
        print("Privacy popup not found.")
    except Exception as ex:
        errorMsg = str(ex)
        print(errorMsg)
        


        
        

    # Sólo se muestran los primeros 30 resultados, hay que volver a usar el webdriver de 
    # Selenium para cargar más resultados hasta que salgan las 100 películas 
    
    # Usamos un set para evitar duplicados en los enlaces
    movie_links = set()
    
    nb_empty_loops = 0
    while len(movie_links) < 100:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        #time.sleep(2)
        try:
            # https://www.browserstack.com/guide/element-click-intercepted-exception-selenium
            
            moreResults_button = driver.find_element(By.CSS_SELECTOR, '.show-more')
            
            driver.execute_script("arguments[0].scrollIntoView();", moreResults_button)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.show-more')))
            
            actions = ActionChains(driver)
            actions.move_to_element(moreResults_button)
            actions.perform()
            actions.click(moreResults_button)
            actions.perform()
            
            if USE_HEADLESS and False:
                # Wait for the element to be clickable
                try:
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.show-more')))
                    moreResults_button.click()
                    print("show-more button clicked")
                except ElementClickInterceptedException as ex:
                    print(f"Failed to click the show-more button - try again: {str(ex)}")
                    #webdriver.ActionChains(driver).move_to_element(moreResults_button ).click(moreResults_button).perform()
                    # Try executing script
                    #driver.execute_script("arguments[0].click();", WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.show-more'))))
                    #driver.execute_script("arguments[0].click();", moreResults_button)
                    
                    driver.execute_script("arguments[0].scrollIntoView();", moreResults_button)
                    moreResults_button.click()
                except Exception as ex:
                    print(f"Failed to click the show-more button: {str(ex)}")
            
            time.sleep(2)
            
            # Move
            if False:
                # Moverse de nuevo al botón
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.show-more')))
                webdriver.ActionChains(driver).move_to_element(moreResults_button )
            
            if False:
                # Verificar que se ha aumentado el scrollHeight
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break

                last_height = new_height
                
        except Exception as ex:
            print(str(ex))
            print("No more results.")
            # Exit the loop
            break
        
        # Extraemos los links de los resultados de la películas
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        has_added_new_links = False
        for a_element in soup.select('.mc-title a'):
            # Check with robots if we can fetch the link
            href = a_element.get('href')
            if rp.can_fetch(user_agent, href):
                if len(movie_links) < 100:
                    if href not in movie_links:
                        movie_links.add(href)
                        has_added_new_links = True
                else:
                    break
                
                
        if has_added_new_links is False:
            # There are no new links
            nb_empty_loops = nb_empty_loops + 1
            if nb_empty_loops >4:
                # Do not keep trying
                break
        else:
            # Reset counter
            nb_empty_loops = 0
    
    driver.quit()

    # Lista para almacenar los datos de las películas
    movies_data = []

    # Extraemos los datos de las 100 películas usando requests porque no tienen ningún elemento complicado
    # y el popup de privacidad ya ha sido aceptado
    
    l = list(movie_links)
    n = len(l)
    for i in tqdm(range(n)):
        movie_link = l[i]
        response = requests.get(movie_link, timeout=10)
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
    fn = os.path.join('dataset','top100_2024films.csv')
    with open(fn, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Posición","Título", "Duración", "País", "Dirección", "Género", "Nota"])
        writer.writerows(movies_data)


