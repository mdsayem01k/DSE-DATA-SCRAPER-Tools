import tkinter as tk

root = tk.Tk()




def volume_up():
    print("Volume Increase +1")

def volume_down():
    print("Volume Decrease -1")

turn_on = tk.Button(root, text="ON")
turn_on.pack()

turn_off = tk.Button(root, text="OFF")
turn_off.pack()

volume = tk.Label(root, text="VOLUME")
volume.pack()

vol_up = tk.Button(root, text="+", command=volume_up)
vol_up.pack()

vol_down = tk.Button(root, text="-", command=volume_down)
vol_down.pack()

root.mainloop()