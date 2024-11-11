#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# cython: language_level=3

"""Common functionality, console and constants
"""


import logging
import rich
from rich.logging import RichHandler
from rich.console import Console

# FORMAT = "%(message)s"
# logging.basicConfig(
#     level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
# )

console = Console()



#
# CONSTANTS
#

CSV_FN = 'top100_2024films.csv'