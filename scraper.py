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

def get_thread_df(driver, id):
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
    thread_df = pd.DataFrame(columns = ['position', 'user', 'comment', 'bid', 'upvote', 'rep', 'seller', 'bidder', 'verified'])
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
        # get upvote
        try:
            upvote = comment.find_element(By.CLASS_NAME, 'interact').text
        except:
            upvote = None

        # get verified
        try: 
            get_verified = comment.find_element(By.CLASS_NAME, 'verified')
        except:
            verified = 0
        else:
            verified = 1

        # get bidder
        try:
            get_bidder = comment.find_element(By.CLASS_NAME, 'bidder')
        except:
            bidder =  0
        else:
            bidder = 1
        
        thread_df.loc[len(thread_df.index)] = [position, username, message, bid, upvote, rep, seller, bidder, verified] 
        position += 1    
    
    return thread_df

def get_basic_df(driver, id):
    """
    Returns a df with basic information about the auction such as:
    Title, subtitle, reserve, number of bids, number of comments, auction end date, nummber of photos
    make, model, year, milage, VIN, title status, location, engine, drivetrain, transmission, 
    body style, exterior color, interior color, seller type
    """
    ### INIT DF ###
    df = pd.DataFrame(columns = ['id', 'title', 'subtitle', 'reserve', 'num_views', 'num_bids', 'num_com', 'end_bid', 'end_date', 'num_photos',
                                'make', 'model', 'milage', 'VIN', 'title', 'location', 'seller', 'engine', 'drivetrain', 'transmission',
                                'body_style', 'e_color', 'i_color', 'seller_type'])
    
    ### NUMBER OF VIEWS ###
                                             #//*[@id="root"]/div[2]/div[5]/div[1]/div[6]/div/ul/li[4]/div[2]
    try:
        num_views = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'td.views-icon'))
        )
    except:
        driver.refresh()
        try:
            num_views = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'td.views-icon'))
            )
        except:
            print("views icon not found after refresh, quitting")
            driver.quit()

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

    df.loc[len(df.index)] = [id, auction_title, subtitle, reserve, num_views, num_bids, num_com, end_bid, end_date, num_photos, make, model, milage, vin, title, location, seller,
                            engine, drivetrain, transmission, body_style, e_color, i_color, seller_type] 

    return df

def get_qanda_df(driver, id):
    """
    Returns a df where each row represents a q and a entry.
    """
    ### INIT DF ###
    df = pd.DataFrame(columns = ['qid', 'question', 'q_author', 'verified', 'answer', 'a_author'])
    if check_exists_by_class_name(driver, 'questions.empty'):
        print('questions empty')
        return df
    questions = driver.find_elements(By.CLASS_NAME, 'qanda.answered')
    i = 1
    for q in questions:
        qid = id + '_' + str(i)
        question = q.find_element(By.XPATH, './/div[1]/div[2]/div').text
        q_author = q.find_element(By.XPATH, './/div[1]/div[1]/div[2]/a').text
        try:
            verified = q.find_element(By.CLASS_NAME, 'verified')
        except:
            verified = 0
        else:
            verified = 1
        answer = q.find_element(By.XPATH, './/div[2]/div[2]/div').text
        a_author = q.find_element(By.XPATH, './/div[2]/div[1]/div[2]/a').text
        df.loc[len(df.index)] = [qid, question, q_author, verified, answer, a_author]
        i += 1
        
    return df

def get_details_df(driver, id):
    detail_wrapper = driver.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[5]/div[1]/div[3]')

    ### DOUGS TAKE ###
    dtake_series = pd.Series()
    try:
        dtake = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section dougs-take']").text
    except: 
        dtake_series.loc[len(dtake_series.index)] = None
        print('dtake not found')
    else:
        dtake_series.loc[len(dtake_series.index)] = dtake

    ### HIGHLIGHTS ###
    high_series = pd.Series()
    try:
        highlights = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-highlights']").find_elements(By.XPATH, './/div/ul/li')
    except:
        high_series.loc[len(high_series.index)] = None
        print('highlights not found')
    else:
        for highlight in highlights:
            high_series.loc[len(high_series.index)] = highlight.text

    ### EQUIPMENT ###
    equip_series = pd.Series()
    try: 
        equipment = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-equipment']").find_elements(By.XPATH, './/div/ul/li')
    except: 
        equip_series.loc[len(equip_series.index)] = None
        print('equipment not found')
    else:
        for equip in equipment:
            equip_series.loc[len(equip_series.index)] = equip.text
    
    ### MODIFICATIONS ###
    mod_series = pd.Series()
    try:
        modifications = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-modifications']").find_elements(By.XPATH, './/div/ul/li')
    except: 
        mod_series.loc[len(mod_series.index)] = None
        print('modifications not found')
    else: 
        for mod in modifications:
            mod_series.loc[len(mod_series.index)] = mod.text

    ### KNOWN FLAWS ###
    flaws_series = pd.Series()
    try:
        known_flaws = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-known_flaws']").find_elements(By.XPATH, './/div/ul/li')
    except:
        flaws_series.loc[len(flaws_series.index)] = None
        print('known flaws not found')
    else:
        for flaw in known_flaws:
            flaws_series.loc[len(flaws_series.index)] = flaw.text

    ### SERVICE HISTORY ###
    service_series = pd.Series()
    try:
        service_hist = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-recent_service_history']").find_elements(By.XPATH, './/div/ul/li')
    except: 
        service_series.loc[len(service_series.index)] = None
        print('service history not found')
    else:
        for ser in service_hist:
            service_series.loc[len(service_series.index)] = ser.text

    ### OTHER ITEMS ###
    other_series = pd.Series()
    try: 
        other_items = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-other_items']").find_elements(By.XPATH, './/div/ul/li')
    except: 
        other_series.loc[len(other_series.index)] = None
        print('other items not found')
    else:
        for other in other_items:
            other_series.loc[len(other_series.index)] = other.text

    ### OWNERSHIP HISTORY ###
    owner_series = pd.Series()
    try:
        ownership_hist = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-ownership_history']").find_element(By.XPATH, './/div/p').text
    except:
        owner_series.loc[len(owner_series.index)] = None
        print('ownership history not found')
    else:
        owner_series.loc[len(owner_series.index)] = ownership_hist

    ### SELLER NOTES ###
    notes_series = pd.Series()
    try:
        seller_notes = detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-seller_notes']").find_elements(By.XPATH, './/div/ul/li')
    except:
        notes_series.loc[len(notes_series)] = None
        print('seller notes not found')
    else:
        for notes in seller_notes:
            notes_series.loc[len(notes_series)] = notes.text

    ### VIDEOS ###
    videos_series = pd.Series()
    try:
        videos = len(detail_wrapper.find_element(By.CSS_SELECTOR, "div[class = 'detail-section detail-videos']").find_elements(By.XPATH, './/div[1]/div'))
    except:
        videos_series.loc[len(notes_series)] = None
        print('videos not found')
    else:
        videos_series.loc[0] = videos


    detail_df = pd.concat([dtake_series, high_series, equip_series, mod_series, flaws_series, service_series, other_series, owner_series, notes_series, videos_series],  
            axis = 1)

    detail_df.columns = ['dtake', 'highlights', 'equipment', 'modifications', 'known_flaws', 'service_history', 'other_items', 'owner_history', 'seller_notes', 'num_videos']
    
    return detail_df

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

    ### BEGIN TRAVERSING PAST AUCTION PAGES ###
    for j in range(80, 215):
        driver.get('https://carsandbids.com/past-auctions/?page=' + str(j)) # auction listings
        time.sleep(2)
        if check_exists_by_xpath(driver, '//*[@id="root"]/div[3]/button/span'):
            driver.find_element(By.XPATH, '//*[@id="root"]/div[3]/button/span').click()

        ### INIT BASIC DF ###
        basic_df = pd.DataFrame() 

        ### BEGIN TRAVERSING PAST AUCION PAGE ###
        for i in range(1, 51):
            id = str(j)+'_'+str(i) # define id
            time.sleep(2)
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

            ### INSIDE AUCTION PAGE ###
            load_and_scroll(driver) # scroll and load entire page
            print('Working id: = ' + str(id))
            basic_df_i = get_basic_df(driver, id) # get basic df
            if basic_df_i.empty:
                driver.back()
            else:
                basic_df = pd.concat([basic_df, basic_df_i], ignore_index=True) # concat basic df

                qanda_df = get_qanda_df(driver, id) # get q and a
                if qanda_df.empty: # if no q and a move on
                    print('no qanda for ' + str(id))
                else:
                    qanda_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\qanda_df\qanda_df_' + str(id) + '.csv') # save q and a df
                
                details_df = get_details_df(driver, id) # get details
                details_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\details_df\details_df' + str(id) + '.csv')
                thread_df = get_thread_df(driver, id) # get comment thread
                thread_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\thread_df\thread_df_' + str(id) + '.csv') # save thread df
                driver.back() # back to auction listings

        basic_df.to_csv(r'C:\Users\franc\Documents\THESIS\scrape_cab\basic_df\basic_df_' + str(j) + '.csv') # save basic df

    driver.quit() # quit driver


if __name__ == '__main__':
    main()