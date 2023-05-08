import re
import datetime
import os
from PIL import Image
from resizeimage import resizeimage
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
SESSION_FOLDER = '../sessions/'
SESSION_FILE = SESSION_FOLDER + 'insta_session.pkl'


def hashtagify(tags):
    result = re.sub(r'(\w+)', r'#\1', tags)
    return result


def tweetable(tweet):
    if len(tweet) > 280:
        print ("This tweet is %d characters. Shortening..." % len(tweet))
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


def instagramableImg(filepath):
    try:
        # Open image file
        img = open(filepath, 'rb')
        with Image.open(img) as image:
            # Validate image format
            if image.format not in ['JPEG', 'PNG', 'BMP']:
                raise ValueError("Invalid image format. Only JPEG, PNG, and BMP formats are supported.")

            # Set target width and height
            width = 1440
            height = 1440

            # Calculate aspect ratios
            ratio_w = width / image.width
            ratio_h = height / image.height

            # Determine resize dimensions
            if ratio_w < ratio_h:
                # Fixed by width
                resize_width = width
                resize_height = round(ratio_w * image.height)
            else:
                # Fixed by height
                resize_width = round(ratio_h * image.width)
                resize_height = height

            # Resize image
            image_resize = image.resize((resize_width, resize_height), Image.ANTIALIAS)

            # Create background image
            background = Image.new('RGBA', (width, height), (255, 255, 255, 255))

            # Calculate offset for centering
            offset = (round((width - resize_width) / 2), round((height - resize_height) / 2))

            # Paste resized image onto background
            background.paste(image_resize, offset)

            # Convert background image to RGB mode
            rgb_result = background.convert('RGB')

            # Generate file path for saved image
            image_dir = "./instagram/"
            os.makedirs(image_dir, exist_ok=True)
            image_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + ".jpeg"
            imagePath = os.path.join(image_dir, image_name)

            # Save image
            rgb_result.save(imagePath)
            return imagePath

    except Exception as e:
        print("Error processing image:", e)
        return None


def tweet_a_pic (filepath, description, tags):
  #Twitter Post
  twitter = Twython(
      consumer_key,
      consumer_secret,
      access_token,
      access_token_secret
  )

  tweetpath = tweetableImg(filepath)
  image = open(tweetpath, 'rb')
  response = twitter.upload_media(media=image)
  media_id = [response['media_id']]
  try:
      tweet = tweetable(description+" "+hashtagify(tags))
      twitter.update_status(status=tweet, media_ids=media_id)
      print("Tweeted: %s" % tweet)
  except Exception as error:
      print('Tweet failed', error)


def flick_a_pic (filepath, title, description, tags):
  #Flickr Post
  flickr = flickrapi.FlickrAPI(api_key, api_secret)
  flickr.authenticate_via_browser(perms='delete')
  try:
      result = flickr.upload(filename=filepath, title=title, description=description, tags=tags)
      print(result.text)
  except Exception as error:
      print('Upload failed', error)
  print("Flickered: %s" % description+" "+tags)


def insta_post (filepath, text, location, lat, lng, tag ):
  # Load session from session file using a context manager
  try:
      with open(SESSION_FILE, 'rb') as f:
          cl = pickle.load(f)
  except FileNotFoundError:
      print(f"Session file not found, creating new session.")
      cl = Client()

  # Log in to Instagram
  cl.login(username, password)

  instaimg = instagramableImg(filepath)

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


def text_formation(title, description, tags, camera, lens, film, lab, scan, date):
  if film :
    film = "🎞️ " + film + ".\n"
  if lab :
    lab = "🧪 " + lab + ".\n"
  if scan :
    scan = "💿 " + scan + ".\n"
  if date :
    date = "🗓️ " + date + ".\n"

  text = title + ".\n.\n📷 " + camera + ".\n👁️ " + lens + ".\n" + film + lab + scan + date + ".\n.\n" + description + ".\n.\n" + hashtagify(tags)
  return text
