import re

def hashtagify(tags):
    result = re.sub(r'(\w+)', r'#\1', tags)
    return result


def tweetable(tweet):
    if len(tweet) > 280:
        print ("This tweet is %d carachters. Shortening..." % len(tweet))
        tweet = tweet[:277]+"..."
    return tweet



