#!/usr/bin/env python

import FinanceDataReader as fdr
import os
import os.path
import time
import numpy as np
import pandas as pd
import datetime as dt
import textwrap
import csv


LIST_FILENAME = "nyse-list.csv"
TARGET = 'NYSE'
DATA_DIR_ROOT = "DATA"

print("NYSE 리스트를 가져옵니다.")
nyse_list = fdr.StockListing(TARGET)
nyse_list.to_csv(LIST_FILENAME)

print(nyse_list.shape)

now = dt.datetime.now()
date = now.strftime("%Y-%m-%d")

data_dir = os.path.join(DATA_DIR_ROOT, date)
os.makedirs(data_dir, exist_ok=True)

for i in nyse_list.itertuples():
    print(f"작업({i.Index}): {i.Symbol.replace('.', '-')} / {i.Name}")
    filename = f"{i.Symbol.replace('.', '-')}.csv"
    file_path = os.path.join(data_dir, filename)

    if os.path.exists(file_path):
        print(f"{file_path}가 이미 있습니다.\n가져오지 않습니다.")
    else:
        print(f"{i.Symbol.replace('.', '-')}를 가져옵니다.")
        data = fdr.DataReader(i.Symbol.replace('.', '-'), "2022")
        data.to_csv(file_path)
        print(f"{i.Symbol.replace('.', '-')}를 가져왔습니다. 잠시 대기합니다.")
        time.sleep(np.random.uniform(0.1, 0.9))

print("모든 항목을 가져왔습니다.")
