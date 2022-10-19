import pandas as pd
import numpy as np
import xmltodict
import requests
from requests_html import HTMLSession
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

page = requests.get("https://carsandbids.com/auctions/3qbOzbzy/2004-porsche-911-gt3")
page.status_code

def load_and_scroll(driver):
    """
    Scrolls and loads more comments until there are no more comments to load.
    This ensures that the full auction page is obtained before doing any further scraping.
    """
    # Scroll to bottom of page to dynamically load everything
    lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    match=False
    while(match==False):
        lastCount = lenOfPage
        time.sleep(3)
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        if lastCount==lenOfPage:
            match=True
    time.sleep(3)

    # find load more comments button and click
    eop = False
    while(eop == False):
        try:
            load_more = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "load-more"))
            )
        except:
            # if no more to load, stop scrolling
            print("end of page reached")
            eop = True
        else:
            # if more to load, click and scroll
            load_more.click()
            lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            match=False
            while(match==False):
                lastCount = lenOfPage
                time.sleep(3)
                lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount==lenOfPage:
                    match=True
            time.sleep(3)
    return None

def get_thread_df(driver):
    """
    Returns a df with information from comment thread including
    position (time), user, comment text, bid value, comment reputation, and whether or not the commenter is the seller.
    """
    # Get comment section
    try:
        main = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comments"))
        )
    except:
        print("Could not find comment section, quitting.")
        driver.quit()

    # get comment thread
    thread = main.find_element(By.CLASS_NAME, 'thread')
    # get each element. could be comment, flagged comment, bid, etc.
    comments = thread.find_elements(By.XPATH, '*')
    # print user of each comment
    thread_df = pd.DataFrame(columns = ['position', 'user', 'comment', 'bid', 'rep', 'seller'])
    position = 1
    for comment in comments:
        # get username
        try:
            username = comment.find_element(By.CLASS_NAME, 'user').text
        except:
            username = None
        # get message
        try: 
            message = comment.find_element(By.CLASS_NAME, 'message').text
        except:
            message = None
        # get bid
        try:
            bid = comment.find_element(By.CLASS_NAME, 'bid-value').text
        except:
            bid = None
        # get reputation
        try:
            rep = comment.find_element(By.CLASS_NAME, 'rep').text
        except:
            bid = None
        # get seller?
        try:
            get_seller = comment.find_element(By.CLASS_NAME, 'seller')
        except:
            seller = 0
        else:
            seller = 1
        
        thread_df.loc[len(thread_df.index)] = [position, username, message, bid, rep, seller] 
        position += 1    
    
    return thread_df

def get_basic_df(driver):
    """
    Returns a df with basic information about the auction such as:
    Title, subtitle, reserve, number of bids, number of comments, auction end date, nummber of photos
    make, model, year, milage, VIN, title status, location, engine, drivetrain, transmission, 
    body style, exterior color, interior color, seller type
    """
    df = pd.DataFrame(columns = ['title,' 'subtitle', 'reserve', 'num_bids', 'num_com', 'end_bid', 'end_date', 'num_photos',
                                'make', 'model', 'milage', 'VIN', 'title', 'location', 'seller', 'engine', 'drivetrain', 'transmission',
                                'body_style', 'e_color', 'i_color', 'seller_type'])
    try:
        auction_heading = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'row auction-heading'))
        )
    except:
        print("Could not find auction heading, quitting.")
        driver.quit()

    title = auction_heading.find_element(By.CLASS_NAME, 'auction-title').text # get title
    subtitle = auction_heading.find_element(By.CLASS_NAME, 'd-md-flex justify-content-between flex-wrap').text # get subtitle
    try: # get reserve 1 or 0
        reserve_text = auction_heading.find_element(By.CLASS_NAME, 'no-reserve')
    except:
        reserve = 1
    else:
        reserve = 0
    
    bid_stats = driver.find_element(By.CLASS_NAME, 'bid-stats')
    num_bids = bid_stats.find_element(By.CLASS_NAME, 'num-bids').find_element(By.CLASS_NAME, 'value').text
    num_com = bid_stats.find_element(By.CLASS_NAME, 'num-comments').find_element(By.CLASS_NAME, 'value').text
    end_bid = bid_stats.find_element(By.CLASS_NAME, 'ended').find_element(By.CLASS_NAME, 'bid-value').text
    end_date = bid_stats.find_element(By.CLASS_NAME, 'time').find_element(By.CLASS_NAME, 'time-ended').text

    photos = driver.find_element(By.CLASS_NAME, 'row auction-photos')
    num_photos = photos.find_element(By.CLASS_NAME, 'group interior').find_element(By.CLASS_NAME, 'all').text

    quick_facts = driver.find_element(By.CLASS_NAME, 'quick-facts')
    make = quick_facts.find_element(By.XPATH, '//dl/dd[1]').text
    model = quick_facts.find_element(By.XPATH, '//dl/dd[2]/a').text
    milage = quick_facts.find_element(By.XPATH, '//dl/dd[3]').text
    vin = quick_facts.find_element(By.XPATH, '//dl/dd[4]').text
    title = quick_facts.find_element(By.XPATH, '//dl/dd[5]').text
    location = quick_facts.find_element(By.XPATH, '//dl/dd[6]').text
    seller = quick_facts.find_element(By.XPATH, '//dl/dd[7]').find_element(By.CLASS_NAME, 'user')
    engine = quick_facts.find_element(By.XPATH, '//dl[2]/dd[1]').text
    drivetrain = quick_facts.find_element(By.XPATH, '//dl[2]/dd[2]').text
    transmission = quick_facts.find_element(By.XPATH, '//dl[2]/dd[3]').text
    body_style = quick_facts.find_element(By.XPATH, '//dl[2]/dd[4]').text
    e_color = quick_facts.find_element(By.XPATH, '//dl[2]/dd[5]').text
    i_color = quick_facts.find_element(By.XPATH, '//dl[2]/dd[6]').text
    seller_type = quick_facts.find_element(By.XPATH, '//dl[2]/dd[7]').find_element(By.CLASS_NAME, 'user')

    df.loc[len(df.index)] = [title, subtitle, reserve, num_bids, num_com, end_bid, end_date, num_photos, make, model, milage, vin, title, location, seller,
                            engine, drivetrain, transmission, body_style, e_color, i_color, seller_type] 

    return df


def main():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) # create driver
    driver.get("https://carsandbids.com/auctions/rxV7kL4j/2002-porsche-911-carrera-coupe") # get webpage
    load_and_scroll(driver)
    #thread_df = get_thread_df(driver)
    #thread_df.to_csv('testdf.csv')
    basic_df = get_basic_df(driver)
    basic_df.to_csv('basicdf.csv')

    driver.quit()


if __name__ == '__main__':
    main()