# 🛒 Blinkit Stock Monitor

A Python bot that automatically monitors a watchlist of Blinkit items and sends you an **email alert** the moment they come back in stock!

-----

## 📌 What it does

- Searches Blinkit for your specified wishlist items every 2 minutes
- Sends a styled email alert when any item is back in stock
- Email includes a direct link to the product page
  
-----

## 🛠️ Tech Stack

- **Python 3.10+**
- **Playwright** — browser automation
- **python-dotenv** — environment variable management
- **smtplib** — email alerts via Gmail SMTP

-----

## ⚙️ Setup Instructions

### Step 1 — Clone the repository

```bash
git clone https://github.com/joycify1/blinkit-stock-monitor.git
cd blinkit-stock-monitor
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### Step 3 — Configure environment variables

Rename `.env.template` to `.env` and fill in your details:

```
GMAIL_SENDER=your@gmail.com
GMAIL_PASSWORD=your_app_password
NOTIFY_EMAIL=your@gmail.com
```

> ⚠️ Use a **Gmail App Password**, not your regular Gmail password.
> Create one at: myaccount.google.com/security → App Passwords

### Step 4 — Add your wishlist items

Open `blinkit_monitor.py` and update the `WATCHLIST`:

```python
WATCHLIST = [
    "Hot Wheels Porsche 911 Carrera Die Cast Car",
    "Your Item Name Here",
]
```

### Step 5 — Login to Blinkit (one time only)

```bash
python blinkit_monitor.py --login
```

A browser will open → log in → press Enter in terminal.

### Step 6 — Start monitoring

```bash
python blinkit_monitor.py
```

-----

## 📧 Email Alert Preview

When an item comes back in stock, you’ll receive a styled email like this:

```
🛒 Blinkit Stock Alert!
1 item is back in stock right now.

Item: Hot Wheels Porsche 911 Carrera
Price: ₹167
[Buy Now →]
```

-----

## 📁 Project Structure

```
blinkit-stock-monitor/
│
├── blinkit_monitor.py     # Main monitoring script
├── requirements.txt       # Python dependencies
├── .env.template          # Environment variables template
├── .gitignore             # Files excluded from Git
└── README.md              # Project documentation
```

-----

## ⚠️ Disclaimer

This project is for **personal and educational use only**.
Web scraping may violate Blinkit’s Terms of Service.
Use responsibly.

-----

## 👩‍💻 Author

Made by **Joyce** — BCA Student, Osmania University, Hyderabad.

-----

## 🌟 Show some love

If you found this useful, give it a ⭐ on GitHub!
