import pytesseract as tesseract
import pandas as pd

pd.set_option('display.max_rows', None)  
pd.set_option('display.max_columns', None) 
pd.set_option('display.width', None)  
pd.set_option('display.max_colwidth', None) 

"""General path, once installed tesseract on computer"""
tesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

text = tesseract.image_to_string("13F/images/UBS.png")

print(text)

