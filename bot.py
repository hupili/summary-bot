import twitter
import re
import jieba
from gensim.summarization import summarize
import requests
import feedparser
import shelve

import config

api = twitter.Api(
    consumer_key=config.consumer_key,
    consumer_secret=config.consumer_secret,
    access_token_key=config.access_token_key,
    access_token_secret=config.access_token_secret)

def strip_html(input):
    output = re.sub('<[^<]+?>', '', input)
    output = output.replace(u'。', u' . ')
    output = output.replace(u'，', u' , ')
    return output

def summarise_and_tweet(entry):
    body = entry['content'][0]['value']
    link = entry['link']

    input = strip_html(body)

    segmented_input = ' '.join(jieba.cut(input))
    # print(segmented_input)
    # print('----')

    summarised_article = summarize(segmented_input, word_count=120)
    summarised_article_compact = summarised_article.replace(' ', '').replace('\n', '')
    short_url_length = api.GetShortUrlLength('https://theinitium.com/newsfeed/')
    text_url_delimeter = ' src: '
    text_more_indicator = '...'
    text_length = 140 - short_url_length - len(text_url_delimeter)
    if len(summarised_article_compact) >= text_length:
        truncated_tweet = summarised_article_compact[:(text_length - len(text_more_indicator))] + text_more_indicator
    else:
        truncated_tweet = summarised_article_compact
    tweet_body = '%s%s%s' % (truncated_tweet, text_url_delimeter, link)
    print(tweet_body)
    #print(len(truncated_tweet))

    status = api.PostUpdate(tweet_body, verify_status_length=False)
    print(status)
    return status

with shelve.open('tweeted-links.db', writeback=True) as myshelf:
    r = requests.get('https://theinitium.com/newsfeed/')
    p = feedparser.parse(r.content)
    #print(p['entries'][0].keys())
    #print(p['entries'][0]['content'][0]['value'])
    body = None
    link = None
    for entry in p['entries'][:10]:
        body = entry['content'][0]['value']
        link = entry['link']
        if not link in myshelf:
            print('Ready to share link: ', link)
            myshelf[link] = {}
            try:
                myshelf[link]['status'] = summarise_and_tweet(entry)
                myshelf[link]['posted'] = True
            except Exception as e:
                myshelf[link]['posted'] = False
                myshelf[link]['exception'] = e
                print('Exception: ', e)
            # One article per execution
            break

