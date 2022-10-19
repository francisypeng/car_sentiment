import pandas as pd
import numpy as np
import xmltodict
import requests
from bs4 import BeautifulSoup

page = requests.get("https://carsandbids.com/auctions/3qbOzbzy/2004-porsche-911-gt3")
page.status_code