import re
import datetime
import os
from PIL import Image
from resizeimage import resizeimage


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
