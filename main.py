import os
import sqlite3
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter import ttk

# Constants
DB_FILE = "password_manager.db"
BACKGROUND_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
HOVER_COLOR = "#45a049"
FONT = ("Helvetica", 12)

# Function to create the database
def create_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create a table for storing credentials if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    encrypted_password TEXT NOT NULL)''')
    
    # Create a table for storing master password and encryption key
    c.execute('''CREATE TABLE IF NOT EXISTS master_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_password TEXT NOT NULL,
                    encryption_key TEXT NOT NULL)''')
    
    conn.commit()
    conn.close()

# Function to authenticate master password
def authenticate():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Retrieve the stored master password and encryption key from the database
    c.execute("SELECT * FROM master_credentials LIMIT 1")
    result = c.fetchone()
    conn.close()

    if not result:
        return None
    
    stored_master_password, stored_encryption_key = result[1], result[2]
    return stored_master_password, stored_encryption_key

# Function to set the master password and encryption key
def set_master_password():
    master_password = askstring("Set Master Password", "Enter a new master password:")
    
    if not master_password:
        messagebox.showwarning("Input Error", "Please enter a master password.")
        return
    
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_master_password = fernet.encrypt(master_password.encode()).decode()
    
    # Save the master password and encryption key to the database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO master_credentials (master_password, encryption_key) VALUES (?, ?)",
              (encrypted_master_password, key.decode()))
    conn.commit()
    conn.close()
    
    messagebox.showinfo("Master Password Set", "Master password set successfully!")

# Function to add a new password
def add_password():
    # Ask for master password if not authenticated
    master_password = askstring("Master Password", "Enter the master password to continue:")
    
    if not master_password:
        messagebox.showwarning("Input Error", "Please enter the master password.")
        return

    result = authenticate()
    if not result:
        messagebox.showerror("Authentication Failed", "No master password set. Please set one.")
        return

    stored_master_password, key = result
    fernet = Fernet(key)

    # Check if entered password matches
    if fernet.decrypt(stored_master_password.encode()).decode() != master_password:
        messagebox.showerror("Authentication Failed", "Incorrect master password.")
        return
    
    account_name = account_name_input.get()
    account_password = account_password_input.get()

    if not account_name or not account_password:
        messagebox.showwarning("Input Error", "Please enter both account name and password.")
        return

    # Encrypt the password
    encrypted_password = fernet.encrypt(account_password.encode()).decode()

    # Store encrypted password in the database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO credentials (account_name, encrypted_password) VALUES (?, ?)",
              (account_name, encrypted_password))
    conn.commit()
    conn.close()
    
    # Clear input fields and show confirmation
    account_name_input.delete(0, tk.END)
    account_password_input.delete(0, tk.END)
    messagebox.showinfo("Password Added", "Password added successfully!")

# Function to view passwords
def view_passwords():
    # Ask for master password if not authenticated
    master_password = askstring("Master Password", "Enter the master password to continue:")
    
    if not master_password:
        messagebox.showwarning("Input Error", "Please enter the master password.")
        return

    result = authenticate()
    if not result:
        messagebox.showerror("Authentication Failed", "No master password set. Please set one.")
        return

    stored_master_password, key = result
    fernet = Fernet(key)

    # Check if entered password matches
    if fernet.decrypt(stored_master_password.encode()).decode() != master_password:
        messagebox.showerror("Authentication Failed", "Incorrect master password.")
        return

    # Fetch all credentials from the database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT account_name, encrypted_password FROM credentials")
    credentials = c.fetchall()
    conn.close()

    if not credentials:
        messagebox.showinfo("No Credentials", "No credentials stored yet.")
        return

    # Create a new window to show the credentials
    view_window = tk.Toplevel(root)
    view_window.title("View Passwords")
    view_window.geometry("400x300")
    view_window.config(bg=BACKGROUND_COLOR)
    
    for account_name, encrypted_password in credentials:
        decrypted_password = fernet.decrypt(encrypted_password.encode()).decode()
        label = tk.Label(view_window, text=f"Account: {account_name}, Password: {decrypted_password}", bg=BACKGROUND_COLOR, font=FONT)
        label.pack(pady=5)

# Create the main window
root = tk.Tk()
root.title("Password Manager")
root.geometry("400x350")
root.config(bg=BACKGROUND_COLOR)

# Check if database exists, if not, create it
if not os.path.exists(DB_FILE):
    create_db()

# Check if the master password is set and if not, ask the user to set it
result = authenticate()
if not result:
    set_master_password()

# Add Buttons and Inputs for Adding/Viewing Credentials
tk.Label(root, text="Account Name", bg=BACKGROUND_COLOR, font=FONT).pack(pady=5)
account_name_input = tk.Entry(root, font=FONT, width=30)
account_name_input.pack(pady=5)

tk.Label(root, text="Account Password", bg=BACKGROUND_COLOR, font=FONT).pack(pady=5)
account_password_input = tk.Entry(root, font=FONT, show="*", width=30)
account_password_input.pack(pady=5)

# Style Buttons
def on_button_hover(event):
    event.widget.config(bg=HOVER_COLOR)

def on_button_leave(event):
    event.widget.config(bg=BUTTON_COLOR)

add_button = tk.Button(root, text="Add Password", font=FONT, bg=BUTTON_COLOR, fg="white", command=add_password)
add_button.pack(pady=10)
add_button.bind("<Enter>", on_button_hover)
add_button.bind("<Leave>", on_button_leave)

view_button = tk.Button(root, text="View Passwords", font=FONT, bg=BUTTON_COLOR, fg="white", command=view_passwords)
view_button.pack(pady=10)
view_button.bind("<Enter>", on_button_hover)
view_button.bind("<Leave>", on_button_leave)

quit_button = tk.Button(root, text="Quit", font=FONT, bg=BUTTON_COLOR, fg="white", command=root.quit)
quit_button.pack(pady=20)
quit_button.bind("<Enter>", on_button_hover)
quit_button.bind("<Leave>", on_button_leave)

root.mainloop()
