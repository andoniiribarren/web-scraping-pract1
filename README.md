# UOC M2.851 Tipología y ciclo de vida de los datos - PR 1

# Target

The target is to create a dataset with data scrapped from a web and publish the dataset in Zenodo.
The web site targeted is https://www.filmaffinity.com/es/ranking.php?rn=ranking_2024_topmovies

# Names

  - Andoni Iribarren González
  - Juan Pedro Rodríguez Nieto

# Repository files

  - source
    - main.py: entry point for the program
    - movie_scraper.py: module to obtain top100_2024 films

# Code instructions

## Environment

The file requirements.min.tx contains the minimum requirements to execute the code
The minimum python version is 3.9; it is recommended to use python3.11
You can create an environment using venv

```bash
python3.11 -m env venv311
```

Then activate the virtual environment with

```bash
source venv311/bin/activate
```

Install the required libraries

```bash
python3.11 -m pip install --upgrade pip -r requirements.min.txt
```


## Execution of the scrapping

The code is designed to be executed from the base directory. Source is in the source directory and results will be stored in the dataset directory
To execute the program use:

```bash
python source/main.py
```

## Publication instructions

Once the dataset has been created, it can be automatically published in a new Zenodo deposition with

```bash
python source/publish.py
```

# Dataset DOI

We have already published the dataset generated, with DOI <https://doi.org/10.5281/zenodo.14078918>

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14078918.svg)](https://doi.org/10.5281/zenodo.14078918)



# License information

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


