import tkinter as tk
from tkinter import messagebox

# Create a hidden root window
root = tk.Tk()
root.withdraw()

# Show the flag in a pop-up
messagebox.showinfo("Flag", "ICTF{pyth0n_3x3_1n_4ds}")

# Ensure the script exits cleanly
root.destroy()