import pytesseract as tesseract
import pandas as pd
import re

pd.set_option('display.max_rows', None)  
pd.set_option('display.max_columns', None) 
pd.set_option('display.width', None)  
pd.set_option('display.max_colwidth', None) 

def show_stocks(img_path):
    # General path, once installed tesseract on computer
    tesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    text = tesseract.image_to_string(img_path)
    print(text)

    lines = text.split("\n")
    lines = [line for line in lines if line.strip() != ""]

    processed_lines = []

    pattern = re.compile(r'^([A-Za-z0-9\s&\.\-]+)\s+(\d+\.\d+%)$')
    
    for line in lines:
        if '(' not in line and ')' not in line:
            match = pattern.match(line)
            if match:
                processed_lines.append(match.group(1).strip())
                processed_lines.append(match.group(2).strip())
                continue
        processed_lines.append(line)
    
    print(processed_lines)

    company_names = [line for line in processed_lines if re.search(r"^(?=.*[a-z])(?=.*[A-Z])[A-Za-z0-9\s&\.\-]+$", line) and len(line) > 4 and "Remove" not in line]
    Percent_Of_Portfolio = [line for line in processed_lines if re.fullmatch(r"\d+\.\d+")]
    Shares_Owned = [line for line in processed_lines if re.fullmatch(r"[\d\.]+[MB]", line)]%", line)]
    Value_owned = [line for line in processed_lines if re.fullmatch(r"\$[\d\.]+[MB]", line)]
    change_in_shares = [line for line in processed_lines if re.search(r"\(.*\)", line) and re.search(r'[a-zA-Z]', line)]
    buy_prices = [line for line in processed_lines if re.search(r"\(.*\)", line) and (line.strip()[-2] == '%' or re.match(r'^\$[\d,\.]+', line))]
    dates = [line for line in processed_lines if re.fullmatch(r"\d{4}-\d{2}-\d{2}", line)]
    
    max_len = max(len(company_names), len(Percent_Of_Portfolio), len(Shares_Owned), len(Value_owned), len(change_in_shares), len(dates))
    
    def pad_list(lst, length):
        return lst + [None] * (length - len(lst))
    
    company_names = pad_list(company_names, max_len)
    Percent_Of_Portfolio = pad_list(Percent_Of_Portfolio, max_len)
    Shares_Owned = pad_list(Shares_Owned, max_len)
    Value_owned = pad_list(Value_owned, max_len)
    change_in_shares = pad_list(change_in_shares, max_len)
    dates = pad_list(dates, max_len)
    
    average_buy_prices = buy_prices[:len(company_names)]
    extra_buy_prices = buy_prices[len(company_names):]
    average_buy_prices = pad_list(average_buy_prices, max_len)
    
    for i in range(min(len(average_buy_prices), len(extra_buy_prices))):
        average_buy_prices[i] = extra_buy_prices[i]
    
    df = pd.DataFrame({
        "Company": company_names,
        "% Of Portfolio": Percent_Of_Portfolio,
        "Shares Owned": Shares_Owned,
        "Value Owned": Value_owned,
        "Change In Shares": change_in_shares,
        "Avg Buy Price": average_buy_prices,
        "Date": dates
    })
    
    print(df)

show_stocks("13F/images/halfpage-ubs.png")