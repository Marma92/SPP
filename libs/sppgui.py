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
    # Get the values of the title and description fields
    title_value = title_field.get()
    description_value = description_field.get()

    # Do something with the form data, e.g. send it to a server or save it to a file
    print("Title:", title_value)
    print("Description:", description_value)

# Create the main window
root = tk.Tk()
root.title("File Upload")

# Set the dimensions of the window to 800x480 pixels
root.geometry("800x480")

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

# Add a "Submit" button
submit_button = tk.Button(form_frame, text="Post", command=submit_form)
submit_button.grid(row=2, column=1, padx=5, pady=5, sticky='e')

# Start the Tkinter event loop
root.mainloop()