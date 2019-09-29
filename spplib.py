import re
import datetime
from PIL import Image
from resizeimage import resizeimage

def hashtagify(tags):
    result = re.sub(r'(\w+)', r'#\1', tags)
    return result


def tweetable(tweet):
    if len(tweet) > 280:
        print ("This tweet is %d carachters. Shortening..." % len(tweet))
        tweet = tweet[:277]+"..."
    return tweet

def tweetableImg(filepath):
    print ("Resizing for a more twitter-friendly format")
    img = open(filepath, 'rb')
    image = Image.open(img)
    image = resizeimage.resize_thumbnail(image, [2048, 2048])
    imagePath = "./resizes/"+datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')+".jpeg"
    image.save(imagePath, image.format)
    return imagePath


