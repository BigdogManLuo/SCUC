import pandas as pd
from io import StringIO

def read_txt_to_dataframe(file_path):
    
    with open(file_path, 'r', encoding='ANSI') as file:
        lines = file.readlines()

    cleaned_lines = []
    for line in lines:
        cleaned_line = '\t'.join(line.split())
        cleaned_lines.append(cleaned_line)

    cleaned_data = "\n".join(cleaned_lines)

    df = pd.read_csv(StringIO(cleaned_data), delimiter='\t')

    return df


bid_capacity = read_txt_to_dataframe('data/instances/1/bidcapacity.txt')
bid_price= read_txt_to_dataframe('data/instances/1/bidprice.txt')
section= read_txt_to_dataframe('data/instances/1/section.txt')
load= read_txt_to_dataframe('data/instances/1/slf.txt')

