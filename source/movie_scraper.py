#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# cython: language_level=3

"""Movie scraper functionality to get the links and data of the top rated movies and generate the dataset
"""


import os
import urllib
import urllib.parse
import urllib.robotparser
from urllib.parse import urljoin

import rich.progress
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *


import rich
from rich.progress import Progress, BarColumn, TextColumn

from rich.table import Table
from rich.pretty import pprint
from bs4 import BeautifulSoup
import time
import requests
import csv
import whois
import builtwith

from tqdm import tqdm


from common import CSV_FN, console

#
# CONSTANTS
#
USE_HEADLESS = False
DEFAULT_CRAWL_DELAY_S = 0.1
TOTAL_MOVIES = 100

def get_whois(url:str) -> dict:
    console.print("\n[bold underline]WhoIs[/]")
    w = whois.whois(url)
    pprint(w, console=console)
    return w

def get_builtwith(url:str) -> dict:
    console.print("\n[bold underline]BuiltWith[/]")
    r = builtwith.builtwith(url)
    pprint(r, console=console)
    return r

def parse_robots(url:str, user_agent:str) -> urllib.robotparser.RobotFileParser:
    robot_url = urljoin(url, "robots.txt")
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
    l = robot_data_raw.decode("utf-8").splitlines()
    rp.parse(l)
    
    
    # Obtener el delay que indica en el fichero robots
    crawl_delay = rp.crawl_delay(user_agent)
    if crawl_delay is None:
        # Establecer 1 como delay porque no hay ninguno especificado en el servidor
        crawl_delay = DEFAULT_CRAWL_DELAY_S
    else:
        # Establecer un mínimo de 1
        crawl_delay = max(DEFAULT_CRAWL_DELAY_S, crawl_delay)

    console.print("\n[bold underline]Robots[/]")
    pprint(l)
    
    return rp, crawl_delay

def get_web(user_agent:str, target_url:str) -> webdriver.Chrome:
    """Get a driver to the target web and click the cookies popup button

    Args:
        user_agent (str): User agent to use for crawling
        target_url (str): Target url

    Returns:
        webdriver.Chrome: driver
    """
    # Usamos selenium para abrir la página porque tiene un popup de privacidad
    # Configuramos las opciones para que no abra el navegador visualmente
    opts = Options()
    if USE_HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--user-agent={user_agent}")

    # Crear el driver y cargar la página
    driver = webdriver.Chrome(options=opts)
    driver.get(target_url)

    #
    # Pulsamos el botón correspondiente a "No aceptar" el popup de privacidad
    #
    try:
        # Esperamos a que aparezca el botón de popup de privacidad
        WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.css-xlut8b')))

        # Hacemos click en el botón
        p_button = driver.find_element(By.CSS_SELECTOR, '.css-xlut8b')
        p_button.click()
        console.print("Privacy popup closed.")
    except TimeoutException as te:
        console.print("Privacy popup not found.")
    except Exception as ex:
        errorMsg = str(ex)
        console.print_exception(errorMsg)
    
    return driver

def get_movie_links(user_agent:str,
                    driver:webdriver.Chrome, 
                    progress:rich.progress.Progress, 
                    rp: urllib.robotparser.RobotFileParser,
                    crawl_delay:float) -> list[str]:
    """Get the movie links from the main ranking page

    The algorithm will push the 'more' button until it gets
    100 results or there are no new results.
    Only links allowed by the robotparser file will be followed

    Args:
        user_agent (str): User agent for the requests
        driver (webdriver.Chrome): selenium driver with the web page loaded
        progress (rich.progress.Progress): progress bar
        rp (urllib.robotparser.RobotFileParser): robot parser to filter url
        crawl_delay (float): delay between requests

    Returns:
        list[str]: list of movies url
    """
    
    # Add task to progress
    task = progress.add_task("Get movie links", total=TOTAL_MOVIES)
    
    # Usamos un set para evitar duplicados en los enlaces
    movie_links = set()
    
    # Sólo se muestran los primeros 30 resultados, hay que volver a usar el webdriver de 
    # Selenium para cargar más resultados hasta que salgan las 100 películas 
    nb_empty_loops = 0
    while len(movie_links) < TOTAL_MOVIES:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
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

            # Add crawl delay
            time.sleep(crawl_delay)

        except Exception as ex:
            console.print(str(ex))
            console.print("No more results.")
            # Exit the loop
            break
        
        # Extraemos los links de los resultados de la películas
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        has_added_new_links = False
        for a_element in soup.select('.mc-title a'):
            # Check with robots if we can fetch the link
            href = a_element.get('href')
            if rp.can_fetch(user_agent, href):
                if len(movie_links) < TOTAL_MOVIES:
                    if href not in movie_links:
                        # This is a new link, add to the list
                        movie_links.add(href)
                        has_added_new_links = True
                        # Update progress
                        progress.advance(task)
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
            
    return movie_links

def process_movie_links(user_agent:str,
                        progress:rich.progress.Progress, 
                        crawl_delay:float,
                        movie_links: list[str]) -> list[list]:
    """Process the list of movie links to retrieve the data of each movie

    Args:
        user_agent (str): User agent for the requests
        progress (rich.progress.Progress): progress bar
        crawl_delay (float): delay between requests
        movie_links (list[str]): list of links to the movie pages

    Returns:
        list[list]: List of movie registers. Each movie register is a list with the following fields
            - index
            - title
            - duration
            - country
            - director
            - genre
            - rating
    """
    # Lista para almacenar los datos de las películas
    movies_data = []

    # Extraemos los datos de las 100 películas usando requests porque no tienen ningún elemento complicado
    # y el popup de privacidad ya ha sido aceptado
    
    task = progress.add_task("Process links", total=TOTAL_MOVIES)
    l = list(movie_links)
    n = len(l)
    headers={'User-Agent':user_agent,}
    for i in range(n):
        movie_link = l[i]
        response = requests.get(movie_link, headers=headers, timeout=10)
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
    
        # Update progress
        progress.advance(task)
    
    return movies_data


def store_dataset(progress:rich.progress.Progress, movies_data:list[list]):
    # Guardamos los datos en un archivo CSV
    task = progress.add_task("Output dataset", total=1)
    fn = os.path.join('dataset', CSV_FN)
    with open(fn, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Posición","Título", "Duración", "País", "Dirección", "Género", "Nota"])
        writer.writerows(movies_data)

    # Update progress
    progress.advance(task)

def movie_scraper():

    
    # https://www.filmaffinity.com/es/ranking.php?rn=ranking_2024_topmovies
    base_url = "https://www.filmaffinity.com"
    target_url = f"{base_url}/es/ranking.php?rn=ranking_2024_topmovies"

    #
    # Preliminar
    #
    console.rule("[bold red]Preliminar")
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    get_whois(base_url)
    get_builtwith(base_url)
    rp, crawl_delay = parse_robots(base_url, user_agent)

    console.print()
    console.rule(f"[bold red]Process {target_url}")

    # Get driver
    driver = get_web(user_agent, target_url)

    with Progress(console=console) as progress:

        # Get movie links
        movie_links = get_movie_links(user_agent, driver, progress, rp, crawl_delay)

        # We will use requests directly to retrieve the movies data so
        # we do not need the driver anymore
        driver.quit()

        # Get the movies data
        movies_data = process_movie_links(user_agent, progress, crawl_delay, movie_links)

        # Save the result
        store_dataset(progress, movies_data)


