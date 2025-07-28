from flask import Flask, render_template, request
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
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
    return content, 200, {'Content-Type': 'text/plain'}

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


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


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    chart = None
    form_data = {}
    active_tab = "simple"  # Default to simple tab
    calculator_type = "sip"  # Default calculator type

    if request.method == 'POST':
        # Check if it's SIP or Lumpsum calculation
        calculator_type = request.form.get('calculator_type', 'sip')
        
        # If POST request, switch to advanced tab and show results
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

            # Create chart for both calculator types
            chart = create_pie_chart(
                result["total_invested"],
                result["net_return"],
                result["fees_paid"],
                result["capital_gains_tax"]
            )

        except Exception as e:
            print("Error:", e)

    else:
        # Set default values for advanced calculator form
        form_data = {
            "monthly_sip": 5000,
            "lumpsum_amount": 100000,
            "annual_return": 0.12,
            "expense_ratio": 0.01,
            "years": 10,
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
