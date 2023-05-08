import tkinter as tk
from tkinter import filedialog
import requests
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

# Create the main window
root = tk.Tk()
root.title("File Upload")

# Set the dimensions of the window to 640x480 pixels
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

# Add a blank label to center the button
blank_label = tk.Label(root)
blank_label.grid(row=2, column=0)

# Start the Tkinter event loop
root.mainloop()