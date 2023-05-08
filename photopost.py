import libs.spplib as spplib
import os
import pickle


#Twitter dependencies
from twython import Twython
from auth.twitterauth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

#Flickr dependencies
import flickrapi
from auth.flickrauth import (
    api_key,
    api_secret
)

#Instagram dependencies
from instagrapi import Client
from auth.instaauth import(
    username,
    password)
from instagrapi.types import Usertag, Location
# Define insta session file path as a variable
SESSION_FOLDER = 'sessions/'
SESSION_FILE = SESSION_FOLDER + 'insta_session.pkl'
share_to_fb = True


print ("Welcome to the simplephotoposter!")
#First, we are going to code a simple script to post at 3 different places:
#Twitter, Flickr, and Instagram

#To do so, we have to :

#chose a file (from a given path)
filepath = input ("Enter a path for your picture to post:")
tweetpath = spplib.tweetableImg(filepath)
image = open(tweetpath, 'rb')

#give it a title
title = input ("Give a title to your picture:")

#give it a description
description = input ("Give a legend to your picture:")

#give it some hashtags
tags = input ("Give it now some tags:")

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
try:
    tweet = spplib.tweetable(description+" "+spplib.hashtagify(tags))
    twitter.update_status(status=tweet, media_ids=media_id)
    print("Tweeted: %s" % tweet)
except Exception as error:
    print('Tweet failed', error)

#Flickr Post
flickr = flickrapi.FlickrAPI(api_key, api_secret)
flickr.authenticate_via_browser(perms='delete')
try:
    result = flickr.upload(filename=filepath, title=title, description=description, tags=tags)
    print(result.text)
except Exception as error:
    print('Upload failed', error)
print("Flickered: %s" % description+" "+tags)

#Instagram Post
camera = input ("Which camera did you use ?")
lens = input ("And which lens ?")
film = input ("Which film did you use ? (leave blank if not)")
lab = input ("Any special lab ? (leave blank if not)")
scan = input ("Who scanned it ? (leave blank if not)")
date = input ("Date of capture? (leave blank if not)")
location = input ("Place of capture? (leave blank if not)")
if location :
    lat = input ("Latitude ?")
    lng = input ("Longitude ?")
tag = input ("Someone to tag? (leave blank if not)")

if film :
    film = "🎞️ " + film + ".\n"
if lab :
    lab = "🧪 " + lab + ".\n"
if scan :
    scan = "💿 " + scan + ".\n"
if date :
    date = "🗓️ " + date + ".\n"

text = title + ".\n.\n📷 " + camera + ".\n👁️ " + lens + ".\n" + film + lab + scan + date + ".\n.\n" + description + ".\n.\n" + spplib.hashtagify(tags)

# Load session from session file using a context manager

try:
    with open(SESSION_FILE, 'rb') as f:
        cl = pickle.load(f)
except FileNotFoundError:
    print(f"Session file not found, creating new session.")
    cl = Client()

# Log in to Instagram
cl.login(username, password)

instaimg = spplib.instagramableImg(filepath)

# Upload photo with optional user tag and location
if tag:
    cl.photo_upload(instaimg, text, [Usertag(user=tag, x=0.5, y=0.5)], location=Location(name=location, lat=lat, lng=lng))
else:
    cl.photo_upload(instaimg, text, location=Location(name=location, lat=lat, lng=lng))

# Save session to session file using a context manager
try:
    os.makedirs(SESSION_FOLDER)
except FileExistsError:
    pass
with open(SESSION_FILE, 'wb') as f:
    pickle.dump(cl, f)
