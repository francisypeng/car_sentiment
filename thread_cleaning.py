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
model = pipeline(model="nlptown/bert-base-multilingual-uncased-sentiment", truncation = True, device=0)
#model = pipeline(model="cardiffnlp/twitter-roberta-base-sentiment-latest")

all_files = glob.glob(os.path.join('thread_df', '*.csv'))

df_out = pd.DataFrame(columns = ['id', 'sentiment_score'])
for file in all_files:
    df = pd.read_csv(file, index_col=0)
    id = file.replace('thread_df\\thread_df_', '').replace('.csv','')
    comments = df.dropna(subset = ['comment']).reset_index(drop=True)
    ds = model(comments['comment'].tolist(), truncation = True)
    #comments.loc[:,'sentiment_score'] = comments['comment'].apply(get_sentiment_score)
    scores = pd.DataFrame(ds)['label'].str.extract('(\d+)').astype(int)
    comments = comments.join(scores).rename(columns={0:'sentiment_score'})
    test = mark_relevant(comments)
    relevant_comments = test[test['relevant'] == True].iloc[1:]
    final_sentiment = relevant_comments.sentiment_score.sum()/len(relevant_comments)
    df_out.loc[len(df_out.index)] = [id, final_sentiment]

df_out.to_csv('thread_sentiment_bert.csv')