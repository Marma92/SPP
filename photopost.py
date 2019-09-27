#Twitter dependencies
from twython import Twython
from twitterauth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

#Flickr dependencies
import flickrapi
from flickrauth import (
    api_key,
    api_secret
)

#Instagram dependencies
from instapy_cli import client
from instaauth import(
    username,
    password)


print ("Welcome to the simplephotoposter!")
#First, we are going to code a simple script to post at 3 different places:
#Twitter, Flickr, and Instagram

#To do so, we have to :

#chose a file (from a given path)
filepath = input ("Enter a path for your picture to post:")
image = open(filepath, 'rb')

#give it a title
title = input ("Give a title to your picture:")

#give it a description
description = input ("Give a legend to your picture:")

#give it some hashtags
hashtags = input ("Give it now some hashtags:")

#POST
print ("And here ya go!")

#Twitter Post
twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

response = twitter.upload_media(media=image)
media_id = [response['media_id']]
twitter.update_status(status=description+" "+hashtags, media_ids=media_id)
print("Tweeted: %s" % description+" "+hashtags)


#Flickr Post
flickr = flickrapi.FlickrAPI(api_key, api_secret)
flickr.authenticate_via_browser(perms='delete')
try:    
    result = flickr.upload(filename=filepath, title=title, description=description, tags=hashtags)
    print(result.text)
except Exception as error:
    print('Upload failed', error)  
print("Flickered: %s" % description+" "+hashtags)


#Instagram Post
camera = input ("Which camera did you use ?")
lens = input ("And which lens ?")
text = title + ".\n.\n" + camera + ".\n" + lens + ".\n.\n" + description + ".\n.\n" + hashtags
with client(username, password) as cli:    cli.upload(filepath, text)
print ("Instagrammed : " + text)

