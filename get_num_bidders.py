import pandas as pd
import numpy as np
import glob
import os
import re

all_files = glob.glob(os.path.join('thread_df', '*.csv'))

df_out = pd.DataFrame(columns = ['id', 'num_bidders'])
for file in all_files:
    df = pd.read_csv(file, index_col=0)
    id = file.replace('thread_df\\thread_df_', '').replace('.csv','')
    bids = df[df['comment'].isnull()].reset_index(drop=True)
    bidders = bids['user'].drop_duplicates()
    bidders.dropna(inplace=True)
    num_bidders = len(bidders)
    df_out.loc[len(df_out.index)] = [id, num_bidders]

df_out.to_csv('num_bidders.csv')