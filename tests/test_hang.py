
import tkinter as tk
import time


def simulate_hang():
    status_label.config(
        text="APPLICATION FROZEN - Testing hang detection..."
    )

    # Update the window before freezing it
    root.update_idletasks()

    print("Test application is now freezing...")
    
    # Deliberately block the GUI thread for 45 seconds
    # This is a controlled test, not a system modification
    time.sleep(45)

    status_label.config(
        text="Application responding again!"
    )

    print("Test application has recovered.")


root = tk.Tk()

root.title("OS Hang Detection - Test Application")
root.geometry("500x250")

heading = tk.Label(
    root,
    text="Application Hang Simulator",
    font=("Arial", 18, "bold")
)
heading.pack(pady=20)

description = tk.Label(
    root,
    text="Click below to simulate an application hang.",
    font=("Arial", 11)
)
description.pack(pady=10)

status_label = tk.Label(
    root,
    text="Status: RESPONDING",
    font=("Arial", 12),
    fg="green"
)
status_label.pack(pady=10)

hang_button = tk.Button(
    root,
    text="SIMULATE APPLICATION HANG",
    command=simulate_hang,
    bg="red",
    fg="white",
    font=("Arial", 11, "bold"),
    padx=10,
    pady=8
)
hang_button.pack(pady=15)

root.mainloop()
