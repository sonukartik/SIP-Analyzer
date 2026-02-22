# 📊 SIP-Analyzer

A Flask-based web application that helps users calculate and visualize returns for multiple investment strategies including SIP, Lumpsum, FD, RD, and SWP.

Built using Python and Flask, this project provides an interactive UI for financial analysis with dynamic chart generation.

---

## 🚀 Features

### 💰 Investment Calculators
- SIP (Systematic Investment Plan)
- Lumpsum Investment
- Fixed Deposit (FD)
- Recurring Deposit (RD)
- Systematic Withdrawal Plan (SWP)

### 📈 Visual Analytics
- Dynamic pie charts for corpus breakdown
- Investment vs returns visualization
- Fee and tax impact representation
- Charts generated using Matplotlib

### 🌐 Web Interface
- Clean HTML templates using Jinja2
- Multiple informational pages (About, Contact, Privacy Policy, Terms)
- Dynamic sitemap generation
- Base64-encoded image rendering for charts

---

## 🛠️ Tech Stack

- Python 3
- Flask
- Matplotlib
- HTML + Jinja2
- CSS

---

## 📂 Project Structure


SIP-Analyzer/
│
├── app.py # Main Flask application
├── templates/ # HTML templates (Jinja2)
├── static/ # Static assets (CSS/images)
├── requirements.txt # Dependencies
└── README.md


---

## ▶️ Running the Project Locally

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sonukartik/SIP-Analyzer.git
cd SIP-Analyzer
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Run the Application
python app.py

Then open in your browser:

http://localhost:5000/
📈 Example Use Case

A user enters:

SIP amount: ₹5,000/month

Expected annual return: 12%

Duration: 10 years

The application calculates:

Total invested amount

Final corpus value

Net returns

Visual breakdown chart
