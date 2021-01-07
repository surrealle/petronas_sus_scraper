from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
import re
import time
from itertools import zip_longest
from bs4 import BeautifulSoup
import requests
from functools import wraps
from requests.exceptions import RequestException
from socket import timeout


driver = webdriver.Chrome(r'C:\chromedriver.exe')
driver.get("http://www.ggar.com/index.php?src=directory&view=rets_agents")
driver.implicitly_wait(10)

class Retry(object):
    """Decorator that retries a function call a number of times, optionally
    with particular exceptions triggering a retry, whereas unlisted exceptions
    are raised.
    :param pause: Number of seconds to pause before retrying
    :param retreat: Factor by which to extend pause time each retry
    :param max_pause: Maximum time to pause before retry. Overrides pause times
                      calculated by retreat.
    :param cleanup: Function to run if all retries fail. Takes the same
                    arguments as the decorated function.
    """
    def __init__(self, times, exceptions=(IndexError), pause=1, retreat=1,
                 max_pause=None, cleanup=None):
        """Initiliase all input params"""
        self.times = times
        self.exceptions = exceptions
        self.pause = pause
        self.retreat = retreat
        self.max_pause = max_pause or (pause * retreat ** times)
        self.cleanup = cleanup

def click_element_XPATH(xpath):
    driver.find_element(By.XPATH,xpath).click()

def failed_call(*args, **kwargs):
    """Deal with a failed call within various web service calls.
    Will print to a log file with details of failed call.
    """
    print("Failed call: " + str(args) + str(kwargs))

retry = Retry(times=5, pause=1, retreat=2, cleanup=failed_call,
              exceptions=(RequestException, timeout))


@retry
def scraper_function():
    try:
        #Go from range 2 - 22
        for row in range(2, 22):
            # CLicks on the name
            time.sleep(1)
            click_element_XPATH(f'//*[@id="rightside"]/table/tbody/tr[{row}]/td[1]/a')
            
            url = driver.current_url
            html_content = requests.get(url).text
            soup = BeautifulSoup(html_content, "lxml")

            # Finds the table
            contact_table = soup.find("table", attrs={"class": "contactInfo"})
            name = soup.find('div', attrs={"class": "retsDetail"}).h2.text
            realtor_info[name] = {}
            # Scrapes all the data in the table
            contact_table_data = contact_table.find_all("td")

            if len(contact_table_data) == 6:
                phone_agency_list = [contact_table_data[1], contact_table_data[5]]
                if realtor_info.get(name):
                    name = name + '2'
                    realtor_info[name] = {}
                    for i in phone_agency_list:
                        if re.match(r'^\d+-\d+-\d+', i.text):
                            realtor_info[name]['phone'] = i.text

                        elif re.match(r'^\w+', i.text):
                            realtor_info[name]['agency'] = i.text

                        else:
                            pass

                else:
                    for i in phone_agency_list:
                        if re.match(r'^\d+-\d+-\d+', i.text):
                            realtor_info[name]['phone'] = i.text

                        elif re.match(r'^\w+', i.text):
                            realtor_info[name]['agency'] = i.text

                        else:
                            pass
                clean = re.findall(r'([a-zA-Z0-9_\-.]+)|@',contact_table_data[3].string)
                email_cleaned = clean[1] + '@' + clean[3] + '.' + clean[5]
                realtor_info[name]['email'] = email_cleaned
                time.sleep(1)

            elif len(contact_table_data) == 2:
                realtor_info[name]['agency'] = contact_table_data[1].text
                time.sleep(1)
            
            else:
                realtor_info[name]['agency'] = contact_table_data[3].text
                
                clean = re.findall(r'([a-zA-Z0-9_\-.]+)|@',contact_table_data[1].string)
                email_cleaned = clean[1] + '@' + clean[3] + '.' + clean[5]
                realtor_info[name]['email'] = email_cleaned
                time.sleep(1)

            # Clicks on the Go Back button
            click_element_XPATH('//*[@id="rightside"]/p[2]/a')
        
        time.sleep(3)
        click_element_XPATH('//*[@id="rightside"]/div[3]/div[1]/div[3]/div[3]/a')
    
    except NoSuchElementException:
        pass

realtor_info = {}
while len(driver.find_elements(By.XPATH, '//*[@id="rightside"]/div[3]/div[1]/div[3]/div[3]/a'))>0:
    scraper_function()

scraper_function()

compiled_df = pd.DataFrame.from_dict({(i): realtor_info[i] 
                                      for i in realtor_info.keys()}, orient = 'index')

compiled_df.index.names = ['Name']

compiled_df.reset_index(inplace = True)

compiled_df.to_csv(r'real_estate_info.csv', index=False, header=True)


