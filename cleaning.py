import pandas as pd
import numpy as np
import glob
import os
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
nltk.download('vader_lexicon')

all_basic_files = glob.glob(os.path.join('details_df', '*.csv'))


### Assemble Detail dfs
df_out = pd.DataFrame(columns=['id', 'num_highlights', 'num_equipment', 'num_modifications', 'num_known_flaws', 'num_service_history', 
                    'num_other_items', 'num_owner_history', 'num_seller_notes', 'num_videos', 'sentiment_score'])

for file in all_basic_files:
    df = pd.read_csv(file, index_col=0)
    id = file.replace('details_df\\details_df', '').replace('.csv','')
    df_count = df.count()
    df_out.loc[len(df_out.index)] = [id, df_count[1], df_count[2], df_count[3], df_count[4], 
                                    df_count[5], df_count[6], df_count[7], df_count[8], df.iloc[0,9]]

df_out.fillna(0, inplace=True)
df_basic = pd.read_csv('basic_df_full.csv', index_col=0)
df_basic_detail = df_basic.merge(df_out, how='left', on='id')

def mark_relevant(dfi):
    df = dfi.copy()
    df['sold_msg'] = df.comment.str.match(pat = '^Sold to .*')
    sold_pos = df.loc[df['sold_msg'] == True].iloc[0,0]
    df['relevant'] = df['position'] >= sold_pos
    df.drop(columns = ['sold_msg'], inplace = True)
    return df

sia = SentimentIntensityAnalyzer()
def get_sentiment_score(text):
    return sia.polarity_scores(text)['compound']

