#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import os,sys,inspect
# currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# parentdir = os.path.dirname(currentdir)
# sys.path.insert(0,parentdir) 

# Setup Logging
from settings import setup_logging
from logging import getLogger

setup_logging()
logger = getLogger('dataset')

from analyzer import preprocess, tokenize

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder

import numpy as np

class Bunch(dict):
    """Container object for datasets: dictionary-like object that
       exposes its keys as attributes."""

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        self.__dict__ = self

def load_semeval(subtask='b', subset='all'):
    try:
        from pymongo import MongoClient
    except ImportError:
        raise ImportError('pymongo must be installed to retrieve data from MongoDB')

    client = MongoClient()
    db = client.twitter_database
    db_labeled_tweets = db.labeled_tweets

    if subtask == 'a':
        raise NotImplementedError('SemEval-2013 Task 2 Subtask A data not yet supported')
    elif subtask == 'b':
        
        q = {
            u'text': {'$exists': True}, 
            u'class.overall': {'$exists': True}
        }

        tweets = list(db_labeled_tweets.find(q))

        vect = CountVectorizer(tokenizer=tokenize, preprocessor=preprocess)#, ngram_range=(1, 2))
        le = LabelEncoder()
        
        if subset == 'all':
            data = vect.fit_transform(tweet.get(u'text') for tweet in tweets)
            target = le.fit_transform(
                [u'neutral' if tweet['class']['overall'] in ('neutral', 'objective', 'objective-OR-neutral') else tweet['class']['overall'] for tweet in tweets]
            )
            docs = tweets
        elif subset == 'train':
            training_tweets = [tweet for tweet in tweets if tweet['class']['training']]
            data = vect.fit_transform(tweet.get(u'text') for tweet in training_tweets)
            target = le.fit_transform(
                [u'neutral' if tweet['class']['overall'] in ('neutral', 'objective', 'objective-OR-neutral') else tweet['class']['overall'] for tweet in training_tweets]
            )
            docs = training_tweets
        elif subset == 'test':
            training_tweets = [tweet for tweet in tweets if tweet['class']['training']]
            vect.fit(tweet.get(u'text') for tweet in training_tweets)
            le.fit(
                [u'neutral' if tweet['class']['overall'] in ('neutral', 'objective', 'objective-OR-neutral') else tweet['class']['overall'] for tweet in training_tweets]
            )
            testing_tweets = [tweet for tweet in tweets if not tweet['class']['training']]
            data = vect.transform(tweet.get(u'text') for tweet in testing_tweets)
            target = le.transform(
                [u'neutral' if tweet['class']['overall'] in ('neutral', 'objective', 'objective-OR-neutral') else tweet['class']['overall'] for tweet in testing_tweets]
            )
            docs = testing_tweets
        else:
            raise ValueError("'{}' is not a valid subset: should be one of ['train', 'test', 'all']".format(subset))
            
    else:
        raise ValueError("'{}' is not a valid subtask: should be one of ['a', 'b']".format(subtask))

    return Bunch(
            data = data,
            target = target,
            target_names = le.classes_,
            label_encoder = le,
            vectorizer = vect,
            docs = np.asarray(docs)
        )



if __name__ == '__main__':
    
    twitter_data = load_semeval(subtask='b', subset='all')
    
    print twitter_data.vectorizer.get_feature_names()
    
    exit(0)
    import matplotlib.pyplot as plt
    import numpy as np

    tweets = load_semeval(subtask='b', subset='all')
    
    bincount = np.bincount(tweets.target)
    
    n = bincount.shape[0]
    
    ind = np.arange(n)  # the x locations for the groups
    width = 0.5         # the width of the bars
    
    #plt.xkcd()
    
    fig, ax = plt.subplots()
    
    rects = ax.bar(ind, bincount, width, align='center', facecolor='#9999ff')
    
    ax.set_ylabel('Frequency')
    ax.set_xlabel('Class')
    ax.set_title('Class frequency distribution')
    ax.set_xticks(ind)
    ax.set_xticklabels(tweets.target_names)
    ax.set_axisbelow(True)
    ax.yaxis.grid()
    
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height+100, '{}'.format(int(height)), ha='center')
    
    plt.savefig('temp.png')