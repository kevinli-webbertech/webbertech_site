import requests
from bs4 import BeautifulSoup

cik = "1350694"
url = f"https://research.secdatabase.com/CIK/{cik}"

headers = {
    "User-Agent": "Your Name (your_email@example.com)"
}

filing_url = "https://www.sec.gov/Archives/edgar/data/1350694/000117266124004671/0001172661-24-004671-index.htm"

# Gets page then finds the infotable.xml with the stock data
response = requests.get(filing_url, headers=headers)

if response.status_code == 200:
  soup = BeautifulSoup(response.text, 'html.parser')
  
  links = soup.find_all('a', href=True)
  
  for link in links:
      href = link.get('href')
      if href.endswith("infotable.xml"): 
          filing_document_url = "https://www.sec.gov/" + href
          print("\nFound filing document URL:", filing_document_url)
else:
  print(f"Failed to get the filing page")
