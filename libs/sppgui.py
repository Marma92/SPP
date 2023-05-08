import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# Event handler for the "Upload" button
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("JPEG files", "*.jpg;*.jpeg")])  # Open a file dialog to select a file
    # Implement file upload logic using the selected file path

    # Display a preview of the selected JPEG image
    image = Image.open(file_path)
    image.thumbnail((320, 320))  # Resize the image to fit within a 320x320 pixel box
    photo = ImageTk.PhotoImage(image)
    image_label.config(image=photo)
    image_label.image = photo

    # Set the size and position of the image label
    image_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

# Event handler for the "Submit" button
def submit_form():
    # Get the values of the form fields
    title_value = title_field.get()
    description_value = description_field.get()
    hashtags_value = hashtags_field.get()
    camera_value = camera_field.get()
    lens_value = lens_field.get()
    film_value = film_field.get()
    lab_value = lab_field.get()
    scan_value = scan_field.get()
    date_value = date_field.get()
    location_value = location_field.get()
    instagram_value = instagram_field.get()
    twitter_value = twitter_field.get()
    flickr_value = flickr_field.get()

    # Do something with the form data, e.g. send it to a server or save it to a file
    print("Title:", title_value)
    print("Description:", description_value)
    print("Hashtags:", hashtags_value)
    print("Camera:", camera_value)
    print("Lens:", lens_value)
    print("Film:", film_value)
    print("Lab:", lab_value)
    print("Scan:", scan_value)
    print("Date:", date_value)
    print("Location:", location_value)

# Create the main window
root = tk.Tk()
root.title("File Upload")

# Set the dimensions of the window to 1000x480 pixels
root.geometry("640x480")

# Add a label to display the preview image
image = Image.new('RGB', (320, 320), 'white')  # Create a white image with the same size as the preview image
photo = ImageTk.PhotoImage(image)
image_label = tk.Label(root, image=photo)
image_label.image = photo
image_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

# Add an "Upload" button
upload_button = tk.Button(root, text="Upload", command=upload_file)
upload_button.grid(row=1, column=0, pady=10, sticky='n', padx=10)

# Add a form to the right of the preview image
form_frame = tk.Frame(root)
form_frame.grid(row=0, column=1, padx=10, pady=10, sticky='n')

# Add a label and entry field for the title
title_label = tk.Label(form_frame, text="Title:")
title_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
title_field = tk.Entry(form_frame)
title_field.grid(row=0, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the description
description_label = tk.Label(form_frame, text="Description:")
description_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
description_field = tk.Entry(form_frame)
description_field.grid(row=1, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the hashtags
hashtags_label = tk.Label(form_frame, text="Hashtags:")
hashtags_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
hashtags_field = tk.Entry(form_frame)
hashtags_field.grid(row=2, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the camera
camera_label = tk.Label(form_frame, text="Camera:")
camera_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')
camera_field = tk.Entry(form_frame)
camera_field.grid(row=3, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the lens
lens_label = tk.Label(form_frame, text="Lens:")
lens_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')
lens_field = tk.Entry(form_frame)
lens_field.grid(row=4, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the film
film_label = tk.Label(form_frame, text="Film:")
film_label.grid(row=5, column=0, padx=5, pady=5, sticky='w')
film_field = tk.Entry(form_frame)
film_field.grid(row=5, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the film lab
lab_label = tk.Label(form_frame, text="Film lab:")
lab_label.grid(row=6, column=0, padx=5, pady=5, sticky='w')
lab_field = tk.Entry(form_frame)
lab_field.grid(row=6, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the scan
scan_label = tk.Label(form_frame, text="Scanning:")
scan_label.grid(row=7, column=0, padx=5, pady=5, sticky='w')
scan_field = tk.Entry(form_frame)
scan_field.grid(row=7, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the date
date_label = tk.Label(form_frame, text="Date:")
date_label.grid(row=8, column=0, padx=5, pady=5, sticky='w')
date_field = tk.Entry(form_frame)
date_field.grid(row=8, column=1, padx=5, pady=5, sticky='w')

# Add a label and entry field for the location
location_label = tk.Label(form_frame, text="Location name:")
location_label.grid(row=9, column=0, padx=5, pady=5, sticky='w')
location_field = tk.Entry(form_frame)
location_field.grid(row=9, column=1, padx=5, pady=5, sticky='w')

instagram_label = tk.Label(form_frame, text="Instagram")
instagram_label.grid(row=10, column=1, padx=5, pady=5, sticky='w')
instagram_field = tk.Checkbutton(form_frame)
instagram_field.grid(row=10, column=0, padx=5, pady=5, sticky='w')

twitter_label = tk.Label(form_frame, text="Twitter")
twitter_label.grid(row=11, column=1, padx=5, pady=5, sticky='w')
twitter_field = tk.Checkbutton(form_frame)
twitter_field.grid(row=11, column=0, padx=5, pady=5, sticky='w')

flickr_label = tk.Label(form_frame, text="Flickr")
flickr_label.grid(row=12, column=1, padx=5, pady=5, sticky='w')
flickr_field = tk.Checkbutton(form_frame)
flickr_field.grid(row=12, column=0, padx=5, pady=5, sticky='w')


# Add a "Submit" button
submit_button = tk.Button(form_frame, text="Submit", command=submit_form)
submit_button.grid(row=13, column=1, padx=5, pady=5, sticky='e')

# Start the Tkinter event loop
root.mainloop()