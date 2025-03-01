import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import pandas as pd
from bs4 import BeautifulSoup
import platform
from functools import lru_cache
import time

"""
Static function: it doesn't rely on self object. This is `this` in java.
We can repurpose this for a lot of other functions for reusability.

Examples:
c = SEC13F()
c.find_common_holdings_multi_cik(['1350694', '1067983', '1037389', '1610520'])
"""
#def aggregate_holdings(*args):
def aggregate_holdings(df_list):
    if not df_list:
        return "No DataFrame/s provided."

    company_sets = [set(df['Company Name']) for df in df_list if 'Company Name' in df.columns]

    if not company_sets:
        return "No 'Company Name' column found in any DataFrame."

    overlapping_stocks = set.intersection(*company_sets)

    if not overlapping_stocks:
        return "No matches found."

    return ", ".join(overlapping_stocks)


class SEC13F:
    headers = {
        "User-Agent": "test@gmail.com"
    }

    __LINUX_CHROME_DRIVER_PATH__ = '/usr/bin/chromedriver'

    def __init__(self):
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)


    # Check if the system is Linux
    @lru_cache(maxsize=256)
    def __is_linux(self):
        if platform.system() == "Linux":
            return True
        else:
            return False

    """
    param: cik_key (https://www.sec.gov/files/company_tickers.json)
    return: the source code of the url of the following,
     
    https://www.sec.gov/edgar/browse/?cik=1350694
    
    For invert and forward search of company name using Edgar Search please refer to the URLs in the README.md in this folder.
    """

    @lru_cache(maxsize=256)
    def __get_page_source(self, cik_key):
        # required to access sec gov pages (via documentation)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('user-data-dir=/tmp/chrome_headless')
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")

        if self.__is_linux():
            driver = webdriver.Chrome(service=Service(self.__LINUX_CHROME_DRIVER_PATH__), options=chrome_options)
        else:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(f"https://www.sec.gov/edgar/browse/?cik={cik_key}")
        driver.implicitly_wait(20)

        page_source = driver.page_source
        driver.quit()
        return page_source

    """ 
    param: cik_key
    return: top holdings of the specified company based on the xml from SEC website.
    Example: https://www.sec.gov/Archives/edgar/data/1350694/000117266125000823/infotable.xml
    
    TODO: We need to break down this functions even more. What is good about this is the nested function definition which 
    hides where it is from being accessed from outside, but the problem of this is that, the function find_htm_link()
    does not only find but it did the essential work. We would like to make sure the function names are actually doing what the
    names tells you to do.
    """
    def find_stock_holdings(self, cik_key):
        page_source = self.__get_page_source(cik_key)
        if page_source is None:
            raise Exception("can't grab the initial html page.")

        soup = BeautifulSoup(page_source, "html.parser")

        # finds first htm link on the sec gov page and then fetches it
        def find_htm_link():
            data_export_div = soup.find("div", {"data-export": "Quarterly report filed by institutional managers, Holdings "})

            if data_export_div:
                a_tag = data_export_div.find_all("a", class_="filing-link-all-files")
                if a_tag:
                    href = a_tag[0].get("href")
                    filing_url = "https://sec.gov" + href
                    print("Found the .htm link:", filing_url)
                    return filing_url
                else:
                    print("No .htm link found within the div.")
            else:
                print("Div with the data-export attribute not found.")

        response = requests.get(find_htm_link(), headers=self.headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            date_div = soup.find('div', class_='formGrouping')
            filing_date = date_div.find('div', class_='info').get_text().strip()

            links = soup.find_all('a', href=True)
            # eg:
            # `url: https://www.sec.gov/Archives/edgar/data/1350694/000117266125000823/0001172661-25-000823-index.htm`
            infotable_links = [link.get('href') for link in links if link.get('href').endswith('.xml')]
            if infotable_links:
                # eg:
                # https://www.sec.gov/Archives/edgar/data/1350694/000117266125000823/infotable.xml
                xml_doc_url = f"https://www.sec.gov/{infotable_links[-1]}"

                print("\nLast XML url:", xml_doc_url)

                xml_response = requests.get(xml_doc_url, headers=self.headers)
                xml_content = xml_response.text
                soup = BeautifulSoup(xml_content, 'xml')
                info_tables = soup.find_all('infoTable')

                data = []
                for info in info_tables:
                    company_name = info.find('nameOfIssuer').text if info.find('nameOfIssuer') else 'None'
                    total_value = int(info.find('value').text) if info.find('value') else 0
                    shares_table = info.find('shrsOrPrnAmt')
                    shares_owned = int(shares_table.find('sshPrnamt').text) if shares_table and shares_table.find('sshPrnamt') else 0

                    data.append({'Company Name': company_name,
                                "Total Value": total_value,
                                "Shares Owned": shares_owned,
                                "Filing Date": filing_date
                                })

                df = pd.DataFrame(data)
                df = df.groupby('Company Name', as_index=False).agg({
                    'Total Value': 'sum',
                    'Shares Owned': 'sum',
                    'Filing Date': 'first'
                })

                df.sort_values(by='Total Value', ascending=False, inplace=True)

                # Convert shares and total value of each stock held into billions(B), millions(M), & K depending on the value
                def divisibleBy(number):
                    string = ''
                    if number >= 1000000000:
                        string =  str(round(number / 1000000000)) + "B"
                    elif number >= 1000000:
                        string = str(round(number / 1000000)) + "M"
                    else:
                        string = str(round(number / 1000)) + "K"
                    return string

                df['Total Value'] = df['Total Value'].astype(str)
                df['Shares Owned'] = df['Shares Owned'].astype(str)

                for index, row in df.iterrows():
                    total_value = int(row['Total Value'])
                    shares_owned = int(row['Shares Owned'])

                    df.at[index, 'Total Value'] = divisibleBy(total_value)
                    df.at[index, 'Shares Owned'] = divisibleBy(shares_owned)

                return df
            else:
                print("No XML files found.")
        else:
            print("Failed to get the filing page")


    """
    TODO: 
        yangyang please try this
    """
    def aggregation_from_sec_xml(self):
        pass


    """"
    TODO:
        Darren please fill out this
    """
    def cik_lookup(list_of_ciks):
        pass

    """
    Finds overlapping stocks based on *args number of stock dataframes placed into the parameter
    Make sure you use the find_stock_holdings() function to generate stock holding dataframes and 
    input them into this function.
    
    Example: 
        c = SEC13F()
        c.find_common_holdings_multi_cik(tuple(['1350694', '1067983', '1037389', '1610520']))
        
    Output: A list of company names, displayed vertically.
    """


    def find_common_holdings_multi_cik(self, list_of_ciks):
        if len(list_of_ciks) == 0:
            raise Exception("Invalid input, please check function definitions.")

        data_frames = []
        for cik in list_of_ciks:
           data_frames.append(self.find_stock_holdings(cik))
        same_holdings = aggregate_holdings(data_frames)

        # TODO Print all original names of the company from CIK
        # company_names = cik_lookup(list_of_ciks)

        print("\n------------------Shared Stock Holdings---------------------")
        shared_holdings = same_holdings.split(",")
        for company in shared_holdings:
            print(company.strip())
        print("\n------------------End Stock Holdings---------------------")


if __name__ == "__main__":
    c = SEC13F()
    start = time.time()
    c.find_common_holdings_multi_cik(tuple(['1350694', '1067983', '1037389', '1610520']))
    end = time.time()
    print("function timing test:"+ str(end - start))
