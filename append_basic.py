import pandas as pd
import numpy as np
import glob
import os

all_files = glob.glob(os.path.join('basic_df', "*.csv"))

df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)

df.drop(columns=['Unnamed: 0'], inplace = True)

df.to_csv('basic_df_full.csv')