#!/usr/bin/env python

import FinanceDataReader as fdr
fdr.__version__
import os
import os.path
import time
import numpy as np
import pandas as pd
import datetime as dt
import textwrap


LIST_FILENAME = "nasdaq-list.csv"
TARGET = 'NASDAQ'
DATA_DIR_ROOT = "DATA"

print("NASDAQ 리스트를 가져옵니다.")
nyse_list = fdr.StockListing(TARGET)
nyse_list.to_csv(LIST_FILENAME)

print(nyse_list.shape)

now = dt.datetime.now()
date = now.strftime("%Y-%m-%d")

data_dir = os.path.join(DATA_DIR_ROOT, date)
os.makedirs(data_dir, exist_ok=True)
