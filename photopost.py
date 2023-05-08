import libs.spplib as spplib
print ("Welcome to the simplephotoposter!")

#chose a file (from a given path)
filepath = input ("Enter a path for your picture to post:")

#give it a title
title = input ("Give a title to your picture:")

#give it a description
description = input ("Give a legend to your picture:")

#give it some hashtags
tags = input ("Give it now some tags:")

#Formatting post text
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
text = spplib.text_formation(title, description, tags, camera, lens, film, lab, scan, date)

#POST
print ("And here ya go!")
spplib.tweet_a_pic(filepath, text)
spplib.flick_a_pic(filepath, title, text, tags)
spplib.insta_post(filepath, text, location, lat, lng, tag)