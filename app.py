import tkinter as tk
from tkinter import messagebox
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Function to fetch stock data from DSE
def fetch_data():
    url = "https://www.dsebd.org/latest_share_price_scroll_l.php"
    response = requests.get(url)

    if response.status_code != 200:
        messagebox.showerror("Error", "Failed to fetch data!")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "table table-bordered background-white shares-table fixedHeader"})
    
    if not table:
        messagebox.showerror("Error", "No data found!")
        return

    data = []
    headers = ["SL", "Trading Code", "LTP", "High", "Low", "Close", "YCP", "Change", "Trade", "Volume"]
    
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        data.append([col.text.strip() for col in cols])

    # Save to CSV
    df = pd.DataFrame(data, columns=headers)
    df.to_csv("dse_stock_data.csv", index=False)
    
    messagebox.showinfo("Success", "Stock data saved to dse_stock_data.csv!")

# GUI setup
root = tk.Tk()
root.title("DSE Data Scraper")
root.geometry("400x300")

label = tk.Label(root, text="DSE Stock Data Scraper", font=("Arial", 14, "bold"))
label.pack(pady=20)

fetch_button = tk.Button(root, text="Fetch Data", command=fetch_data, font=("Arial", 12), bg="blue", fg="white")
fetch_button.pack(pady=10)

exit_button = tk.Button(root, text="Exit", command=root.quit, font=("Arial", 12), bg="red", fg="white")
exit_button.pack(pady=10)

root.mainloop()
