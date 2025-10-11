from flask_mail import Mail, Message
import os
from flask import Flask, render_template, request, flash
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
# It's a good practice to set a secret key for flashing messages
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-default-secret-key')

# Mail Configuration - Best to use environment variables for sensitive data
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') # For Gmail, use an "App Password"
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')
try:
    mail = Mail(app)
except Exception as e:
    print(f"Error sending email: {e}") # For debugging
    flash('There was an error sending your message. Please try again later.', 'danger')

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message_body = request.form.get('message')

        try:
            msg = Message(
                subject=f"New Contact Form Message from {name}",
                recipients=[os.environ.get('EMAIL_USER')],  # Send to yourself
                body=f"From: {name} <{email}>\n\n{message_body}"
            )
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            print(f"Error sending email: {e}") # For debugging
            flash('There was an error sending your message. Please try again later.', 'danger')

        return render_template("contact.html")
    return render_template("contact.html")
    
@app.route('/googled31b5d709c031016.html')
def google_verify():
    return 'google-site-verification: googled31b5d709c031016.html', 200

@app.route('/robots.txt')
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",  # Allow all pages to be crawled

        "User-agent: Mediapartners-Google", # Specifically for AdSense
        "Allow: /"
    ]
    return "\n".join(lines), 200, {'Content-Type': 'text/plain'}

@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-3229320652703762, DIRECT, f08c47fec0942fa0"
    response = app.make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

@app.route("/about")
def about():
    return render_template("about.html")

# Utility function to format with Lakhs/Cr
def format_full_with_unit(value):
    formatted_full = f"{value:,.2f}"
    if value >= 1e7:
        unit = f"{value / 1e7:.2f} Cr"
    elif value >= 1e5:
        unit = f"{value / 1e5:.2f} Lakh"
    else:
        unit = None
    return f"{formatted_full} ({unit})" if unit else formatted_full

# Register the filter
app.jinja_env.filters['with_unit'] = format_full_with_unit


def calculate_sip(monthly_sip, annual_return, expense_ratio, years, inflation_rate, ltcg_rate=0, stcg_rate=0):
    total_months = years * 12
    values = np.zeros(total_months + 1)

    monthly_return = (1 + annual_return) ** (1 / 12) - 1

    for month in range(1, total_months + 1):
        values[month] = (values[month - 1] + monthly_sip) * (1 + monthly_return)
        if month % 12 == 0:  # Deduct expense ratio yearly
            values[month] *= (1 - expense_ratio)

    gross_corpus = values[-1]
    total_invested = monthly_sip * total_months

    # For calculating fees paid (no expense ratio)
    values_no_fee = np.zeros(total_months + 1)
    for month in range(1, total_months + 1):
        values_no_fee[month] = (values_no_fee[month - 1] + monthly_sip) * (1 + monthly_return)

    corpus_no_fee = values_no_fee[-1]
    fees_paid = max(0, corpus_no_fee - gross_corpus)

    # Calculate capital gains
    capital_gains = max(0, gross_corpus - total_invested)
    
    # Calculate capital gains tax based on investment duration
    if years > 1:
        # Long Term Capital Gains (LTCG) - applies after 1 year
        # LTCG is taxed on gains exceeding Rs. 1 Lakh per financial year.
        taxable_ltcg = max(0, capital_gains - 100000)
        capital_gains_tax = taxable_ltcg * ltcg_rate
        tax_type = "LTCG"
    else:
        # Short Term Capital Gains (STCG) - applies for investments <= 1 year
        capital_gains_tax = capital_gains * stcg_rate
        tax_type = "STCG"
    
    # Corpus after capital gains tax
    corpus_after_tax = gross_corpus - capital_gains_tax

    # Inflation impact (applied to corpus after tax)
    inflation_impact = max(0, corpus_after_tax * (1 - (1 / ((1 + inflation_rate) ** years))))
    final_corpus = corpus_after_tax - inflation_impact
    final_corpus = max(0, min(final_corpus, corpus_after_tax))

    net_return = max(0, corpus_after_tax - total_invested)

    return {
        "total_invested": round(total_invested, 2),
        "gross_corpus": round(corpus_no_fee, 2),
        "fees_paid": round(fees_paid, 2),
        "capital_gains": round(capital_gains, 2),
        "capital_gains_tax": round(capital_gains_tax, 2),
        "tax_type": tax_type,
        "corpus_after_tax": round(corpus_after_tax, 2),
        "inflation_adjusted_final_corpus": round(final_corpus, 2),
        "final_corpus": round(gross_corpus, 2),
        "net_return": round(net_return, 2),
    }


def calculate_lumpsum(lumpsum_amount, annual_return, expense_ratio, years, inflation_rate, ltcg_rate=0, stcg_rate=0):
    """Calculate lumpsum investment returns with tax considerations"""
    
    # Calculate gross corpus without fees
    gross_corpus_no_fee = lumpsum_amount * ((1 + annual_return) ** years)
    
    # Calculate gross corpus with annual expense ratio deduction
    gross_corpus = lumpsum_amount
    for year in range(years):
        gross_corpus *= (1 + annual_return)
        gross_corpus *= (1 - expense_ratio)  # Deduct expense ratio annually
    
    # Calculate fees paid
    fees_paid = max(0, gross_corpus_no_fee - gross_corpus)
    
    # Calculate capital gains
    capital_gains = max(0, gross_corpus - lumpsum_amount)
    
    # Calculate capital gains tax based on investment duration
    if years > 1:
        # Long Term Capital Gains (LTCG) - applies after 1 year
        # LTCG is taxed on gains exceeding Rs. 1 Lakh per financial year.
        taxable_ltcg = max(0, capital_gains - 100000)
        capital_gains_tax = taxable_ltcg * ltcg_rate
        tax_type = "LTCG"
    else:
        # Short Term Capital Gains (STCG) - applies for investments <= 1 year
        capital_gains_tax = capital_gains * stcg_rate
        tax_type = "STCG"
    
    # Corpus after capital gains tax
    corpus_after_tax = gross_corpus - capital_gains_tax
    
    # Inflation impact (applied to corpus after tax)
    inflation_impact = max(0, corpus_after_tax * (1 - (1 / ((1 + inflation_rate) ** years))))
    final_corpus = corpus_after_tax - inflation_impact
    final_corpus = max(0, min(final_corpus, corpus_after_tax))
    
    net_return = max(0, corpus_after_tax - lumpsum_amount)
    
    return {
        "total_invested": round(lumpsum_amount, 2),
        "gross_corpus": round(gross_corpus_no_fee, 2),
        "fees_paid": round(fees_paid, 2),
        "capital_gains": round(capital_gains, 2),
        "capital_gains_tax": round(capital_gains_tax, 2),
        "tax_type": tax_type,
        "corpus_after_tax": round(corpus_after_tax, 2),
        "inflation_adjusted_final_corpus": round(final_corpus, 2),
        "final_corpus": round(gross_corpus, 2),
        "net_return": round(net_return, 2),
    }


def calculate_fd(principal_amount, annual_interest_rate, years, compounding_frequency):
    """Calculate Fixed Deposit returns - simplified version without tax calculations"""
    
    # Convert frequency string to number
    frequency_map = {
        'yearly': 1,
        'half-yearly': 2, 
        'quarterly': 4,
        'monthly': 12,
        'daily': 365
    }
    
    n = frequency_map.get(compounding_frequency, 4)  # Default to quarterly
    
    # Calculate maturity amount using compound interest formula
    # A = P(1 + r/n)^(nt)
    maturity_amount = principal_amount * ((1 + annual_interest_rate / n) ** (n * years))
    
    # Calculate interest earned
    interest_earned = maturity_amount - principal_amount
    
    # Calculate effective annual rate
    effective_rate = ((maturity_amount / principal_amount) ** (1 / years) - 1) * 100
    
    return {
        "principal_amount": round(principal_amount, 2),
        "maturity_amount": round(maturity_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round(effective_rate, 2)
    }


def calculate_rd(monthly_deposit, annual_interest_rate, years, compounding_frequency):
    """Calculate Recurring Deposit returns"""
    
    # Convert frequency string to number
    frequency_map = {
        'yearly': 1,
        'half-yearly': 2, 
        'quarterly': 4,
        'monthly': 12,
        'daily': 365
    }
    
    n = frequency_map.get(compounding_frequency, 4)  # Default to quarterly
    total_months = years * 12
    
    # For RD, we need to calculate the compound interest for each monthly deposit
    # Each deposit earns interest for different durations
    maturity_amount = 0
    
    # Calculate maturity amount for each monthly deposit
    for month in range(1, total_months + 1):
        # Time remaining for this deposit to earn interest (in years)
        time_remaining = (total_months - month + 1) / 12
        
        # Calculate maturity value for this monthly deposit
        if time_remaining > 0:
            deposit_maturity = monthly_deposit * ((1 + annual_interest_rate / n) ** (n * time_remaining))
            maturity_amount += deposit_maturity
        else:
            maturity_amount += monthly_deposit
    
    # Total invested amount
    total_invested = monthly_deposit * total_months
    
    # Interest earned
    interest_earned = maturity_amount - total_invested
    
    # Calculate effective annual rate
    effective_rate = ((maturity_amount / total_invested) ** (1 / years) - 1) * 100
    
    return {
        "monthly_deposit": round(monthly_deposit, 2),
        "total_invested": round(total_invested, 2),
        "maturity_amount": round(maturity_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round(effective_rate, 2)
    }


def calculate_swp(initial_corpus, monthly_withdrawal, annual_return, expense_ratio, inflation_rate=0):
    """Calculate SWP (Systematic Withdrawal Plan) scenarios"""
    
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    
    corpus = initial_corpus
    total_withdrawn = 0
    month = 0
    monthly_withdrawals = []
    corpus_values = []
    
    current_withdrawal = monthly_withdrawal
    
    # Calculate until corpus is exhausted or 50 years (600 months)
    while corpus > 0 and month < 600:
        month += 1
        
        # Apply returns first
        corpus *= (1 + monthly_return)
        
        # Apply expense ratio annually (every 12 months)
        if month % 12 == 0:
            corpus *= (1 - expense_ratio)
        
        # Adjust withdrawal for inflation if enabled
        if inflation_rate > 0 and month > 1:
            current_withdrawal *= (1 + monthly_inflation)
        
        # Make withdrawal
        actual_withdrawal = min(current_withdrawal, corpus)
        corpus -= actual_withdrawal
        total_withdrawn += actual_withdrawal
        
        # Store data for visualization
        monthly_withdrawals.append(actual_withdrawal)
        corpus_values.append(corpus)
        
        # Break if corpus becomes very small
        if corpus < 1:
            break
    
    # Calculate average monthly withdrawal
    avg_monthly_withdrawal = total_withdrawn / month if month > 0 else 0
    
    # Calculate total returns earned during withdrawal period
    total_returns = total_withdrawn + corpus - initial_corpus
    
    return {
        "initial_corpus": round(initial_corpus, 2),
        "monthly_withdrawal": round(monthly_withdrawal, 2),
        "total_withdrawn": round(total_withdrawn, 2),
        "remaining_corpus": round(corpus, 2),
        "duration_months": month,
        "duration_years": round(month / 12, 1),
        "avg_monthly_withdrawal": round(avg_monthly_withdrawal, 2),
        "total_returns_earned": round(total_returns, 2),
        "corpus_exhausted": corpus < 1,
        "monthly_withdrawals": monthly_withdrawals[:60],  # First 5 years for chart
        "corpus_values": corpus_values[:60]  # First 5 years for chart
    }


def create_pie_chart(total_invested, net_return, fees_paid, capital_gains_tax):
    labels = ['Invested Amount', 'Net Return', 'Fees', 'Capital Gains Tax']
    values = [total_invested, net_return, fees_paid, capital_gains_tax]
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
    
    # Filter out zero values for cleaner chart
    filtered_data = [(label, value, color) for label, value, color in zip(labels, values, colors) if value > 0]
    
    if filtered_data:
        labels, values, colors = zip(*filtered_data)
        
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
        plt.title("Investment Corpus Breakdown (Including Taxes)")
    else:
        plt.figure(figsize=(8, 8))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Investment Corpus Breakdown")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data


def create_fd_pie_chart(principal_amount, interest_earned):
    """Create a simple pie chart for FD showing principal and interest"""
    labels = ['Principal Amount', 'Interest Earned']
    values = [principal_amount, interest_earned]
    colors = ['#3498db', '#2ecc71']
    
    if interest_earned > 0:
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
        plt.title("Fixed Deposit Breakdown")
    else:
        plt.figure(figsize=(8, 8))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Fixed Deposit Breakdown")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data


def create_rd_pie_chart(total_invested, interest_earned):
    """Create a simple pie chart for RD showing total invested and interest"""
    labels = ['Total Invested', 'Interest Earned']
    values = [total_invested, interest_earned]
    colors = ['#9b59b6', '#e67e22']
    
    if interest_earned > 0:
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
        plt.title("Recurring Deposit Breakdown")
    else:
        plt.figure(figsize=(8, 8))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Recurring Deposit Breakdown")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data

def create_simple_pie_chart(total_invested, net_return):
    """Create a simple pie chart showing only invested amount and net return."""
    labels = ['Total Invested', 'Net Return']
    values = [total_invested, net_return]
    colors = ['#3498db', '#2ecc71']
    
    # Filter out zero/negative values for a cleaner chart
    filtered_data = [(label, value, color) for label, value, color in zip(labels, values, colors) if value > 0]
    
    if filtered_data:
        labels, values, colors = zip(*filtered_data)
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title("Investment vs. Return")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data

def create_swp_chart(corpus_values, monthly_withdrawals):
    """Create a line chart showing corpus depletion over time"""
    months = list(range(1, len(corpus_values) + 1))
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Corpus value over time
    ax1.plot(months, corpus_values, color='#e74c3c', linewidth=2, marker='o', markersize=3)
    ax1.set_title('Corpus Value Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Months')
    ax1.set_ylabel('Corpus Value (₹)')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
    
    # Monthly withdrawal amounts
    ax2.plot(months, monthly_withdrawals, color='#2ecc71', linewidth=2, marker='s', markersize=3)
    ax2.set_title('Monthly Withdrawal Amount', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Months')
    ax2.set_ylabel('Withdrawal Amount (₹)')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    chart = None
    form_data = {}
    active_tab = "simple"  # Default to simple tab
    calculator_type = "sip"  # Default calculator type for advanced tab

    if request.method == 'POST':
        # Check which form was submitted
        form_type = request.form.get('form_type', 'advanced')
        
        if form_type == 'advanced':
            # Advanced form submission
            calculator_type = request.form.get('calculator_type', 'sip')
            active_tab = "advanced"
            
            try:
                if calculator_type == 'sip':
                    form_data = {
                        "monthly_sip": int(request.form['monthly_sip']),
                        "annual_return": float(request.form['annual_return']) / 100,
                        "expense_ratio": float(request.form['expense_ratio']) / 100,
                        "years": int(request.form['years']),
                        "inflation_rate": float(request.form.get('inflation_rate', 0)) / 100,
                        "ltcg_rate": float(request.form.get('ltcg_rate', 0)) / 100,
                        "stcg_rate": float(request.form.get('stcg_rate', 0)) / 100,
                    }
                    result = calculate_sip(**form_data)
                    chart = create_pie_chart(
                        result["total_invested"],
                        result["net_return"],
                        result["fees_paid"],
                        result["capital_gains_tax"]
                    )
                
                elif calculator_type == 'lumpsum':
                    form_data = {
                        "lumpsum_amount": int(request.form['lumpsum_amount']),
                        "annual_return": float(request.form['annual_return']) / 100,
                        "expense_ratio": float(request.form['expense_ratio']) / 100,
                        "years": int(request.form['years']),
                        "inflation_rate": float(request.form.get('inflation_rate', 0)) / 100,
                        "ltcg_rate": float(request.form.get('ltcg_rate', 0)) / 100,
                        "stcg_rate": float(request.form.get('stcg_rate', 0)) / 100,
                    }
                    result = calculate_lumpsum(**form_data)
                    chart = create_pie_chart(
                        result["total_invested"],
                        result["net_return"],
                        result["fees_paid"],
                        result["capital_gains_tax"]
                    )

            except Exception as e:
                print("Error:", e)

        elif form_type == 'fd':
            # FD form submission - simplified without tax options
            active_tab = "fd"
            
            try:
                form_data = {
                    "principal_amount": int(request.form['fd_principal_amount']),
                    "annual_interest_rate": float(request.form['fd_annual_interest_rate']) / 100,
                    "years": int(request.form['fd_years']),
                    "compounding_frequency": request.form['fd_compounding_frequency']
                }
                result = calculate_fd(**form_data)
                chart = create_fd_pie_chart(
                    result["principal_amount"],
                    result["interest_earned"]
                )
                calculator_type = "fd"  # Set for template rendering

            except Exception as e:
                print("Error:", e)

        elif form_type == 'rd':
            # RD form submission - simplified without tax options
            active_tab = "rd"
            
            try:
                form_data = {
                    "monthly_deposit": int(request.form['rd_monthly_deposit']),
                    "annual_interest_rate": float(request.form['rd_annual_interest_rate']) / 100,
                    "years": int(request.form['rd_years']),
                    "compounding_frequency": request.form['rd_compounding_frequency']
                }
                result = calculate_rd(**form_data)
                chart = create_rd_pie_chart(
                    result["total_invested"],
                    result["interest_earned"]
                )
                calculator_type = "rd"  # Set for template rendering

            except Exception as e:
                print("Error:", e)

        elif form_type == 'swp':
            # SWP form submission
            active_tab = "swp"
            
            try:
                form_data = {
                    "initial_corpus": int(request.form['swp_initial_corpus']),
                    "monthly_withdrawal": int(request.form['swp_monthly_withdrawal']),
                    "annual_return": float(request.form['swp_annual_return']) / 100,
                    "expense_ratio": float(request.form.get('swp_expense_ratio', 0)) / 100,
                    "inflation_rate": float(request.form.get('swp_inflation_rate', 0)) / 100,
                }
                result = calculate_swp(**form_data)
                if result["corpus_values"] and result["monthly_withdrawals"]:
                    chart = create_swp_chart(
                        result["corpus_values"],
                        result["monthly_withdrawals"]
                    )
                calculator_type = "swp"  # Set for template rendering

            except Exception as e:
                print("Error:", e)
        elif form_type == 'simple':
            # Simple form submission
            active_tab = "simple"
            calculator_type = request.form.get('calculator_type', 'sip')
            
            try:
                if calculator_type == 'sip':
                    form_data = {
                        "monthly_sip": int(request.form['monthly_sip']),
                        "annual_return": float(request.form['annual_return']) / 100,
                        "expense_ratio": float(request.form.get('expense_ratio', 1)) / 100,
                        "years": int(request.form['years']),
                        "inflation_rate": float(request.form.get('inflation_rate', 6)) / 100,
                        "ltcg_rate": float(request.form.get('ltcg_rate', 10)) / 100,
                        "stcg_rate": float(request.form.get('stcg_rate', 15)) / 100,
                    }
                    result = calculate_sip(**form_data)
                    chart = create_simple_pie_chart(
                        result["total_invested"],
                        result["final_corpus"] - result["total_invested"]
                    )
                
                elif calculator_type == 'lumpsum':
                    form_data = {
                        "lumpsum_amount": int(request.form['lumpsum_amount']),
                        "annual_return": float(request.form['annual_return']) / 100,
                        "expense_ratio": float(request.form.get('expense_ratio', 1)) / 100,
                        "years": int(request.form['years']),
                        "inflation_rate": float(request.form.get('inflation_rate', 6)) / 100,
                        "ltcg_rate": float(request.form.get('ltcg_rate', 10)) / 100,
                        "stcg_rate": float(request.form.get('stcg_rate', 15)) / 100,
                    }
                    result = calculate_lumpsum(**form_data)
                    chart = create_simple_pie_chart(
                        result["total_invested"],
                        result["final_corpus"] - result["total_invested"]
                    )

            except Exception as e:
                print("Error:", e)
    else:
        # Set default values for forms
        form_data = {
            "monthly_sip": 5000,
            "lumpsum_amount": 100000,
            "principal_amount": 100000,
            "monthly_deposit": 5000,
            "initial_corpus": 1000000,
            "monthly_withdrawal": 10000,
            "annual_return": 0.12,
            "annual_interest_rate": 0.07,
            "expense_ratio": 0.01,
            "years": 10,
            "compounding_frequency": "quarterly",
            "inflation_rate": 0.06,
            "ltcg_rate": 0.10,
            "stcg_rate": 0.15
        }

    return render_template('index.html', 
                         result=result, 
                         chart=chart, 
                         form_data=form_data, 
                         active_tab=active_tab,
                         calculator_type=calculator_type)


if __name__ == '__main__':
    app.run(debug=True)
