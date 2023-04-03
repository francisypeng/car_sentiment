import pandas as pd
import numpy as np
import glob
import os
import re

def mark_relevant(dfi):
    df = dfi.copy()
    df['sold_msg'] = df.comment.str.match(pat = '^Sold to .*')
    if df['sold_msg'].astype(int).sum() == 0:
        df['sold_msg'] = df.comment.str.match(pat = '^Reserve not met.*')
    sold_pos = df.loc[df['sold_msg'] == True].iloc[0,0]
    df['relevant'] = df['position'] >= sold_pos
    df.drop(columns = ['sold_msg'], inplace = True)
    return df

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
sentiment_pipeline = pipeline("sentiment-analysis", truncation = True)
#model = pipeline(model="nlptown/bert-base-multilingual-uncased-sentiment", truncation = True, device=0)
model = pipeline(model="cardiffnlp/twitter-roberta-base-sentiment-latest", device = 0, max_length=512)

all_files = glob.glob(os.path.join('thread_df', '*.csv'))

for file in all_files:
    df = pd.read_csv(file, index_col=0)
    id = file.replace('thread_df\\thread_df_', '').replace('.csv','')
    comments = df.dropna(subset = ['comment']).reset_index(drop=True)
    ds = model(comments['comment'].tolist(), truncation = True)
    #comments.loc[:,'sentiment_score'] = comments['comment'].apply(get_sentiment_score)
    #scores = pd.DataFrame(ds)['label'].str.extract('(\d+)').astype(int)
    scores = pd.DataFrame(ds)['label'].apply(lambda x: 1 if x == 'positive' else (0 if x == 'neutral' else -1))
    #comments = comments.join(scores).rename(columns={0:'sentiment_score'})
    comments = comments.join(scores).rename(columns={'label':'sentiment_score'})
    test = mark_relevant(comments)
    relevant_comments = test[test['relevant'] == True].iloc[1:]
    relevant_comments.to_csv('sentiment_df/sentiment_df_' + str(id) + '.csv')
    

