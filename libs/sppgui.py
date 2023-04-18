import tkinter as tk
from tkinter import filedialog
import requests

# Event handler for the "Upload" button
def upload_file():
    file_path = filedialog.askopenfilename()  # Open a file dialog to select a file
    # Implement file upload logic using the selected file path
    # For example, you can use the 'requests' library to make a POST request with the file
    with open(file_path, 'rb') as file:
        response = requests.post('http://example.com/upload', files={'file': file})
        print(response.text)  # Print the response from the server

# Create the main window
root = tk.Tk()
root.title("File Upload")

# Add a label
label = tk.Label(root, text="Select a file to upload:")
label.pack(pady=10)

# Add an "Upload" button
upload_button = tk.Button(root, text="Upload", command=upload_file)
upload_button.pack()

# Start the Tkinter event loop
root.mainloop()