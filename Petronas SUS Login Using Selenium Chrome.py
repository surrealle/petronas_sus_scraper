#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

driver = webdriver.Chrome(r'C:\chromedriver.exe')
username = input('Please key in username')
password = input('Please key in password')

# Converts Aging file into a dataframe
ds=pd.read_excel('Test Petronas Aging.xlsx')

# Fills any error in the created Dataframe with 'None'
ds.fillna('None', inplace = True)


#Cleans specific columns in the dataframe because pandas add decimals for some reason
def cleaning_columns(column_name):
    try:
        cleaned_so = ds[column_name].astype(str).str.split('.', n = 1, expand = True)
        cleaned_so.columns = [column_name, 'Non-' + column_name]
        ds[column_name] = cleaned_so[column_name]

    except ValueError:
        pass

cleaning_columns('SO')
cleaning_columns('DO')
cleaning_columns('Inv_No')


#try:
    #cleaned_so = ds['SO'].astype(str).str.split('.', n = 1, expand = True)
    #cleaned_so.columns = ['SO', 'Non-SO']
    #ds['SO'] = cleaned_so['SO']
#except ValueError:
    #pass

#try:
    #cleaned_do = ds['DO'].astype(str).str.split('.', n = 1, expand = True)
    #cleaned_do.columns = ['DO', 'Non-DO']
    #ds['DO'] = cleaned_do['DO']
#except ValueError:
    #pass

#try:
    #cleaned_inv = ds['Inv_No'].astype(str).str.split('.', n = 1, expand = True)
    #cleaned_inv.columns = ['Inv_No', 'Non-Inv']
    #ds = ds.drop(['Inv_No'], axis = 1)
    #ds['Inv_No'] = cleaned_inv['Inv_No']
#except ValueError:
    #pass
#replaces the dirty columns and add the cleaned columns


#Takes out the PO numbers from the dataframe to be used as reference
po_list = ds['PO_No'].unique().tolist()

#SAP code for the customers to be checked
east_msia_codes = [10021578,10021701, 10023994, 10021818]
west_msia_codes = [10021783, 10021810, 10021811, 10021818, 10021837,
                       10022061, 10022457, 10022458, 10022466, 10024745, 10025415]

#Separates the list to be checked to East & West Malaysia. 
#Because DO number for East Msia starts with 4, while for West Msia starts with 8
east_msia_list = ds[ds['Customer'].isin(east_msia_codes)]
west_msia_list = ds[ds['Customer'].isin(west_msia_codes)]

#Navigate to website
driver.get("https://supplier-selfservice.petronas.com.my/irj")
driver.implicitly_wait(10)

#Checking the boxes and entering credentials
driver.find_element(By.ID,("cb_agree")).click()
driver.find_element(By.ID,("cb_agree2")).click()
user_element = driver.find_element(By.ID,"logonuidfield")
user_element.send_keys(username)
pass_element = driver.find_element(By.ID,"logonpassfield")
pass_element.send_keys(password)
driver.find_element(By.ID,("uidPasswordLogon")).click()

driver.implicitly_wait(30)

#Function to navigate and locate PO up until document flow
def search_po_homepage():
    #Clicking Find on SUS Homepage
    driver.switch_to.frame("contentAreaFrame")
    time.sleep(10)
    driver.implicitly_wait(20)
    driver.switch_to.frame(0)
    driver.switch_to.frame(0)
    driver.find_element(By.XPATH, "//*[@id='utility_search']/span").click()

    driver.implicitly_wait(10)

def enter_po_search(i):
    #Enter PO number and click search button
    driver.implicitly_wait(10)
    enter_po = driver.find_element(By.ID,"search_searchPONumber")
    enter_po.clear()
    enter_po.send_keys(i)   
    driver.find_element(By.XPATH, "//*[@id='search_SearchButton']/span").click()
    driver.implicitly_wait(10)
    
    #To handle NoSuchElementException in case of error from non-standard PO numbers
    try:
        #Clicks the PO number
        driver.find_element(By.XPATH, "//*[@id='order.list_order_list_order_list[1].ref_doc_no']/span").click()
        driver.implicitly_wait(10)
        
        #Clicks the document flow link
        driver.find_element(By.XPATH, "//td[7]/a/span").click()
        
        #Scrapes the required columns from the Document Flow table
        doc_type = driver.find_elements(By.XPATH, "//*[@id='docflow.list_DocFlowList']/tbody/tr/td/table/tbody/tr/td[1]")
        doc_no = driver.find_elements(By.XPATH, "//*[@id='docflow.list_DocFlowList']/tbody/tr/td/table/tbody/tr/td[2]")
        doc_name = driver.find_elements(By.XPATH, "//*[@id='docflow.list_DocFlowList']/tbody/tr/td/table/tbody/tr/td[3]")
        doc_date = driver.find_elements(By.XPATH, "//*[@id='docflow.list_DocFlowList']/tbody/tr/td/table/tbody/tr/td[4]")
        doc_value = driver.find_elements(By.XPATH, "//*[@id='docflow.list_DocFlowList']/tbody/tr/td/table/tbody/tr/td[6]")

        #Iterates through list created from the scraped columns in a parallel manner
        for (j,k,l, m, n) in zip_longest(doc_name, doc_type,doc_no, doc_date, doc_value):
            
            #Takes out the SO/DO number from the column doc_name
            so_number = re.findall(r'\d+', j.text)
            
            #Takes out the text from the column doc_name
            cleaning = re.findall(r'[a-zA-Z]+\s[a-zA-Z]+-[a-zA-Z]+|[a-zA-Z]+\s[a-zA-Z]+|[a-zA-Z]+', j.text)
            
            #checks if the value in the column doc_name starts with 9, which means it's an invoice
            invoice_test = re.match(r'[9]+', j.text)
            
            #Checks if the text 'Goods Received' is in variable cleaning
            if 'Goods Received' in cleaning and len(so_number) > 0:
                #Since variable so_number returns a list, gotta take the number out from the list as a string
                x = so_number.pop()
                
                #Checks if [PO][SO/DO] is already created in the dictionary
                #Also checks if [PO][SO/DO] : 'Goods Received' already exists to check for duplicates
                if po_numbah[i].get(x) and po_numbah[i][x].get('Goods Received'):
                    po_numbah[i][x]['Goods_Received_Duplicate'] = 'True'
                    po_numbah[i][x]['SUS_GR_Duplicate_Type'] = k.text
                    po_numbah[i][x]['SUS_GR_Duplicate_No'] = l.text
                    po_numbah[i][x]['SUS_GR_Duplicate_Date'] = m.text
                    po_numbah[i][x]['SUS_GR_Duplicate_Value'] = n.text
                
                #Checks if [PO][SO/DO] is already created in the dictionary
                #This is in case Goods Acceptance appear first before Goods Received
                elif po_numbah[i].get(x) and not po_numbah[i][x].get('Goods Received'):
                    po_numbah[i][x]['Goods_Received'] = 'True'
                    po_numbah[i][x]['SUS_GR_Type'] = k.text
                    po_numbah[i][x]['SUS_GR_No'] = l.text
                    po_numbah[i][x]['SUS_GR_Date'] = m.text
                    po_numbah[i][x]['SUS_GR_Value'] = n.text
                
                #If neither of the above conditions is exists then a [PO][SO/DO] key is created
                else:
                    po_numbah[i][x] = {}
                    po_numbah[i][x]['Goods_Received'] = 'True'
                    po_numbah[i][x]['SUS_GR_Type'] = k.text
                    po_numbah[i][x]['SUS_GR_No'] = l.text
                    po_numbah[i][x]['SUS_GR_Date'] = m.text
                    po_numbah[i][x]['SUS_GR_Value'] = n.text
            
            
            elif 'Goods Accepted' in cleaning and len(so_number) > 0:
                x = so_number.pop()
                if po_numbah[i].get(x) and not po_numbah[i][x].get('Goods_Accepted'):
                    po_numbah[i][x]['Goods_Accepted'] = 'True'
                    po_numbah[i][x]['SUS_GA_Type'] = k.text
                    po_numbah[i][x]['SUS_GA_No'] = l.text
                    po_numbah[i][x]['SUS_GA_Date'] = m.text
                    po_numbah[i][x]['SUS_GA_Value'] = n.text
                                
                elif po_numbah[i].get(x) and po_numbah[i][x].get('Goods_Accepted'):
                    po_numbah[i][x]['Goods_Accepted_Duplicate'] = 'True'
                    po_numbah[i][x]['SUS_GA_Duplicate_Type'] = k.text
                    po_numbah[i][x]['SUS_GA_Duplicate_No'] = l.text
                    po_numbah[i][x]['SUS_GA_Duplicate_Date'] = m.text
                    po_numbah[i][x]['SUS_GA_Duplicate_Value'] = n.text
                            
                else:
                    po_numbah[i][x] = {}
                    po_numbah[i][x]['Goods_Accepted'] = 'True'
                    po_numbah[i][x]['SUS_GA_Type'] = k.text
                    po_numbah[i][x]['SUS_GA_No'] = l.text
                    po_numbah[i][x]['SUS_GA_Date'] = m.text
                    po_numbah[i][x]['SUS_GA_Value'] = n.text
        
            elif 'Goods Received-Reversal' in cleaning and len(so_number) > 0:
                x = so_number.pop()
                if po_numbah[i].get(x):
                    po_numbah[i][x]['Goods_Received_Reversal'] = 'True'
                    po_numbah[i][x]['SUS_GR_Reversal_Type'] = k.text
                    po_numbah[i][x]['SUS_GR_Reversal_No'] = l.text
                    po_numbah[i][x]['SUS_GR_Reversal_Date'] = m.text
                    po_numbah[i][x]['SUS_GR_Reversal_Value'] = n.text    

                else:
                    po_numbah[i][x] = {}
                    po_numbah[i][x]['Goods_Received_Reversal'] = 'True'
                    po_numbah[i][x]['SUS_GR_Reversal_Type'] = k.text
                    po_numbah[i][x]['SUS_GR_Reversal_No'] = l.text
                    po_numbah[i][x]['SUS_GR_Reversal_Date'] = m.text
                    po_numbah[i][x]['SUS_GR_Reversal_Value'] = n.text
                
            elif 'Goods Accepted-Reversal' in cleaning and len(so_number) > 0:
                x = so_number.pop()
            
                if po_numbah[i].get(x):
                    po_numbah[i][x]['Goods_Accepted_Reversal'] = 'True'
                    po_numbah[i][x]['SUS_GA_Reversal_Type'] = k.text
                    po_numbah[i][x]['SUS_GA_Reversal_No'] = l.text
                    po_numbah[i][x]['SUS_GA_Reversal_Date'] = m.text
                    po_numbah[i][x]['SUS_GA_Reversal_Value'] = n.text
            
                else:
                    po_numbah[i][x] = {}
                    po_numbah[i][x]['Goods_Accepted_Reversal'] = 'True'    
                    po_numbah[i][x]['SUS_GA_Reversal_Type'] = k.text
                    po_numbah[i][x]['SUS_GA_Reversal_No'] = l.text
                    po_numbah[i][x]['SUS_GA_Reversal_Date'] = m.text
                    po_numbah[i][x]['SUS_GA_Reversal_Value'] = n.text
        
            elif invoice_test:
                x = so_number.pop()
                
                if po_numbah[i].get(x):
                    po_numbah[i][x]['Invoice'] = 'True'
                    po_numbah[i][x]['SUS_Doc_Type'] = k.text
                    po_numbah[i][x]['SUS_PaymentRequest_No'] = l.text
                    po_numbah[i][x]['SUS_PaymentRequest_Date'] = m.text
                    po_numbah[i][x]['SUS_PaymentRequest_Value'] = n.text
                    
                else:
                    po_numbah[i][x] = {}
                    po_numbah[i][x]['Invoice'] = 'True'
                    po_numbah[i][x]['SUS_Doc_Type'] = k.text
                    po_numbah[i][x]['SUS_PaymentRequest_No'] = l.text
                    po_numbah[i][x]['SUS_PaymentRequest_Date'] = m.text
                    po_numbah[i][x]['SUS_PaymentRequest_Value'] = n.text
            
            elif 'Goods Received' not in cleaning and len(so_number) > 0:
                x = so_number.pop()
                po_numbah[i][x] = {}
                po_numbah[i][x]['Goods_Received'] = 'False'
                po_numbah[i][x]['SUS_Doc_Type'] = k.text
                po_numbah[i][x]['SUS_Doc_No'] = l.text
                po_numbah[i][x]['SUS_Doc_Date'] = m.text
                po_numbah[i][x]['SUS_Doc_Value'] = n.text
        
            elif 'Goods Accepted' not in cleaning and len(so_number) > 0:
                x = so_number.pop()
                po_numbah[i][x] = {}
                po_numbah[i][x]['Goods_Accepted'] = 'False'
                po_numbah[i][x]['SUS_Doc_Type'] = k.text
                po_numbah[i][x]['SUS_Doc_No'] = l.text
                po_numbah[i][x]['SUS_Doc_Date'] = m.text
                po_numbah[i][x]['SUS_Doc_Value'] = n.text
     
        #Clicks Find button
        driver.find_element(By.XPATH, "//*[@id='breadcrumb_susBreadCrumb']/a[2]/span").click()
        
    except NoSuchElementException:
        #When non-standard PO number is entered, this will return the browser to the Find page
        driver.find_element(By.XPATH, "//*[@id='breadcrumb_susBreadCrumb']/a[2]/span").click()


search_po_homepage()

#Created a dictionary named po_numbah
po_numbah = {}

#Changes values in the dataframe that was converted from excel into strings
ds = ds.astype(str)
for i in po_list:
    po_numbah[i] = {}
    po_no = i
    enter_po_search(i)

#Creates a dataframe from the dictionary containing the cleaned data
#Sets PO number and SO/DO number as the indices for the dataframe to group them by PO and SO/DO
compiled_df = pd.DataFrame.from_dict({(i,j): po_numbah[i][j] 
                                      for i in po_numbah.keys() 
                                      for j in po_numbah[i].keys()}, orient = 'index')

#Names the indices column
compiled_df.index.names = ['PO', 'SO']

#Resets the dataframe so it repeats
compiled_df.reset_index(inplace = True)

#Replace NaN with None instead
compiled_df.fillna('None', inplace = True)

#Joins the Aging and the data scraped from SUS website
#Drops the unrequired columns
#Fills
east_msia_checking = east_msia_list.astype(str).merge(compiled_df.astype(str), on = 'SO', how = 'left')
east_msia_checking.drop(['Invoice', 'SUS_Doc_Type', 'SUS_PaymentRequest_No', 'SUS_PaymentRequest_Date', 
                         'SUS_PaymentRequest_Value'], axis = 1, inplace = True)
east_msia_checking.fillna('None', inplace = True)

west_msia_checking = west_msia_list.astype(str).merge(compiled_df.astype(str), left_on = 'DO', right_on = 'SO', how = 'left')
west_msia_checking.drop(['Invoice', 'SUS_Doc_Type', 'SUS_PaymentRequest_No', 'SUS_PaymentRequest_Date', 
                         'SUS_PaymentRequest_Value'], axis = 1, inplace = True)
west_msia_checking.fillna('None', inplace = True)

inv_checking = ds.astype(str).merge(compiled_df.astype(str), left_on = 'Inv_No', right_on = 'SO', how = 'left')
inv_checking = inv_checking.iloc[:, [0,1,2,3,4,6, 7, 8, 19, 20, 21, 22, 23]]
inv_checking.fillna('None', inplace = True)

east_msia_checking = east_msia_checking.astype(str).merge(inv_checking.astype(str), left_on = 'SO', 
                                                          right_on = 'SO_x', how = 'left')
east_msia_checking.drop(['PO_x', 'PO_No_y', 'SO_x', 'DO_y', 'Customer_y', 'Document_Date_y', 
                         'Inv_No_y', 'PO_y', 'SUS_GA_Value_y'], axis = 1, inplace = True)



west_msia_checking = west_msia_checking.astype(str).merge(inv_checking.astype(str), left_on = 'DO', 
                                                          right_on = 'DO', how = 'left')
west_msia_checking.drop(['PO_x', 'SO_y', 'PO_No_y', 'SO_x_y', 'Customer_y', 'Document_Date_y', 
                         'Inv_No_y', 'PO_y', 'SUS_GA_Value_y'], axis = 1, inplace = True)

east_msia_checking.to_csv(r'east msia sus1.csv', index=False, header=True)
west_msia_checking.to_csv(r'west msia sus1.csv', index=False, header=True)
inv_checking.to_csv(r'inv sus1.csv', index=False, header=True)

driver.quit()

