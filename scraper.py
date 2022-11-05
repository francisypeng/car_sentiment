import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException  
import time

#test commit 3

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
            rep = None
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
    ### INIT DF ###
    df = pd.DataFrame(columns = ['title', 'subtitle', 'reserve', 'num_bids', 'num_com', 'end_bid', 'end_date', 'num_photos',
                                'make', 'model', 'milage', 'VIN', 'title', 'location', 'seller', 'engine', 'drivetrain', 'transmission',
                                'body_style', 'e_color', 'i_color', 'seller_type'])
    
    ### TITLE, SUBTITLE, RESERVE Y/N ###
    auction_heading = driver.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[1]')
    try:
        auction_title_obj = WebDriverWait(auction_heading, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "auction-title"))
        )
    except:
        print("Could not find auction-title, quitting.")
        driver.quit()
    #auction_title_obj = auction_heading.find_element(By.CLASS_NAME, 'auction-title') # get title
    auction_title = auction_title_obj.find_element(By.XPATH, '//h1').text
    subtitle = auction_heading.find_element(By.XPATH, '//div/div[2]/h2').text # get subtitle
    try: # get reserve 1 or 0
        reserve_text = auction_heading.find_element(By.CLASS_NAME, 'no-reserve')
    except:
        reserve = 1
    else:
        reserve = 0

    ### BID STATS: # bids, # comments, $ final bid, end date ###
    if check_exists_by_xpath(driver, '//*[@id="root"]/div[2]/div[3]/div[1]/div/div/ul/li[1]/span[2]'):
        if driver.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[3]/div[1]/div/div/ul/li[1]/span[2]').text == 'Auction Cancelled':
            return df
    bid_stats = driver.find_element(By.CLASS_NAME, 'bid-stats')
    num_bids = bid_stats.find_element(By.CLASS_NAME, 'num-bids').find_element(By.CLASS_NAME, 'value').text
    num_com = bid_stats.find_element(By.CLASS_NAME, 'num-comments').find_element(By.CLASS_NAME, 'value').text
    end_bid = bid_stats.find_element(By.CLASS_NAME, 'ended').find_element(By.CLASS_NAME, 'value').text
    end_date = bid_stats.find_element(By.CLASS_NAME, 'time').find_element(By.CLASS_NAME, 'time-ended').text

    ### NUMBER OF PHOTOS ###
    photos = driver.find_element(By.CLASS_NAME, 'gallery-preview')
    num_photos = photos.find_element(By.CLASS_NAME, 'images').find_element(By.CLASS_NAME, 'all').text

    ### QUICK FACTS TABLE ###
    quick_facts = driver.find_element(By.CLASS_NAME, 'quick-facts')
    make = quick_facts.find_element(By.XPATH, '//dl/dd[1]').text
    model = quick_facts.find_element(By.XPATH, '//dl/dd[2]/a').text
    milage = quick_facts.find_element(By.XPATH, '//dl/dd[3]').text
    vin = quick_facts.find_element(By.XPATH, '//dl/dd[4]').text
    title = quick_facts.find_element(By.XPATH, '//dl/dd[5]').text
    location = quick_facts.find_element(By.XPATH, '//dl/dd[6]').text
    seller = quick_facts.find_element(By.XPATH, '//dl/dd[7]').find_element(By.CLASS_NAME, 'user').text
    engine = quick_facts.find_element(By.XPATH, '//dl[2]/dd[1]').text
    drivetrain = quick_facts.find_element(By.XPATH, '//dl[2]/dd[2]').text
    transmission = quick_facts.find_element(By.XPATH, '//dl[2]/dd[3]').text
    body_style = quick_facts.find_element(By.XPATH, '//dl[2]/dd[4]').text
    e_color = quick_facts.find_element(By.XPATH, '//dl[2]/dd[5]').text
    i_color = quick_facts.find_element(By.XPATH, '//dl[2]/dd[6]').text
    seller_type = quick_facts.find_element(By.XPATH, '//dl[2]/dd[7]').text

    df.loc[len(df.index)] = [auction_title, subtitle, reserve, num_bids, num_com, end_bid, end_date, num_photos, make, model, milage, vin, title, location, seller,
                            engine, drivetrain, transmission, body_style, e_color, i_color, seller_type] 

    return df

def check_exists_by_class_name(driver, class_name):
    try:
        driver.find_element(By.CLASS_NAME, class_name)
    except NoSuchElementException:
        return False
    return True

def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True

def main():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) # create driver
    driver.maximize_window() # maximize window for consistency
    for j in range(10, 193):
        driver.get('https://carsandbids.com/past-auctions/?page=' + str(j)) # auction listings
        time.sleep(2)
        if check_exists_by_xpath(driver, '//*[@id="root"]/div[3]/button/span'):
            driver.find_element(By.XPATH, '//*[@id="root"]/div[3]/button/span').click()
        basic_df = pd.DataFrame() # initialize df
        for i in range(1, 51):
            xpath = '//*[@id="root"]/div[2]/div[2]/div/ul[1]/li[' + str(i) + ']/div[2]/div/a' # auction element xpath
            try:
                auction = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath)) # find auction
                )
            except:
                print("Could not find auction from past auction page, quitting.")
                driver.quit()

            action = ActionChains(driver) # initialize action chains driver for scroll to element and click
            action.move_to_element(auction).click().perform() # scroll to element and click

            load_and_scroll(driver) # scroll and load entire page
            basic_df_i = get_basic_df(driver) # get basic df
            if basic_df_i.empty:
                driver.back()
            else:
                basic_df = pd.concat([basic_df, basic_df_i], ignore_index=True) # concat basic df
                thread_df = get_thread_df(driver) # get comment thread
                thread_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\thread_df\thread_df_' + str(j) + '_' + str(i) + '.csv') # save thread df
                driver.back() # back to auction listings

        basic_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\basic_df\basic_df_' + str(j) + '.csv') # save basic df

    driver.quit() # quit driver


if __name__ == '__main__':
    main()