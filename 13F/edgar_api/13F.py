import requests
import pandas as pd
from bs4 import BeautifulSoup

pd.set_option('display.max_rows', None)  
pd.set_option('display.max_columns', None)  
pd.set_option('display.width', None) 
pd.set_option('display.max_colwidth', None) 

# required to input email as header to access sec edgar api
headers = {
    "User-Agent": "darrenliu101@gmail.com"
}

company_tickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
ciks = company_tickers.json()['0']['cik_str']

company_data = pd.DataFrame.from_dict(company_tickers.json(), orient='index')
#To see all the tickers and titles
print(company_data)


#CIK, put in company name to get it, print(company_data) to find your desired company
input_ticker = "ubs"
normal_cik = company_data.loc[company_data['ticker'] == input_ticker.upper() , 'cik_str']
normal_cik = normal_cik.iloc[0] if not normal_cik.empty else None 
print(f"Ticker found: {normal_cik}")


#actual cik has leading zeros so fill
cik = str(normal_cik).zfill(10)

meta_data = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers=headers)

#print(meta_data.json()['filings']['recent'].keys())

forms = pd.DataFrame.from_dict(meta_data.json()['filings']['recent'])

#print(forms[['accessionNumber','reportDate','form']].head(50))

# find accession number for most recent 13F-HR
form_13f = forms[forms['form'] == '13F-HR']
sorted_form_13f = form_13f.sort_values(by='reportDate', ascending=False)
accession_number = sorted_form_13f.iloc[0]['accessionNumber']
accession_number_no_dashes = accession_number.replace('-', '')

filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_dashes}/{accession_number}-index.htm"
print(filing_url)

response = requests.get(filing_url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = soup.find_all('a', href=True)
    infotable_links = [link.get('href') for link in links if link.get('href').endswith(('.xml'))]
    
    if infotable_links:
        xml_doc_url = f"https://www.sec.gov/{infotable_links[-1]}"
        print("\nLast XML url:", xml_doc_url)
        
        xml_response = requests.get(xml_doc_url, headers=headers)
        xml_content = xml_response.text
        soup = BeautifulSoup(xml_content, 'xml')
        info_tables = soup.find_all('infoTable')
        
        data = []

        for info in info_tables:
            company_name = info.find('nameOfIssuer').text if info.find('nameOfIssuer') else 'None'
            total_value = info.find('value').text if info.find('value') else 'None'
            shares_table = info.find('shrsOrPrnAmt')
            
            if shares_table:
                shares_owned = shares_table.find('sshPrnamt').text if shares_table.find('sshPrnamt') else 'None'
            else:
                shares_owned = 'None'
            
            data.append({'Company Name': company_name,
                         "Total Value": total_value,
                         "Shares Owned": shares_owned})

        df = pd.DataFrame(data)
        
        print(df)
        
    else:
        print("No xml files found.")
else:
    print("Failed to get the filing page")

