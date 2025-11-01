import os
from flask import Flask, render_template, request, make_response
from datetime import datetime, timedelta
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

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
            # Email functionality disabled for now
            # msg = Message(...)
            # mail.send(msg)
            pass
        except Exception as e:
            print(f"Error sending email: {e}")

        return render_template("contact.html")
    return render_template("contact.html")
    
@app.route('/googled31b5d709c031016.html')
def google_verify():
    return 'google-site-verification: googled31b5d709c031016.html', 200

@app.route('/robots.txt')
def robots_txt():
    """Enhanced robots.txt for better crawling"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /private/",
        "",
        "User-agent: Mediapartners-Google",
        "Allow: /",
        "",
        f"Sitemap: {request.url_root}sitemap.xml",
        "",
        "# Crawl-delay for good SEO practices",
        "Crawl-delay: 1"
    ]
    response = make_response("\n".join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap for better SEO"""
    pages = []
    ten_days_ago = (datetime.now() - timedelta(days=10)).date().isoformat()
    
    # Define static pages manually
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/about', 'priority': '0.8', 'changefreq': 'weekly'},
        {'url': '/contact', 'priority': '0.7', 'changefreq': 'monthly'},
        {'url': '/disclaimer', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/privacy', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/terms', 'priority': '0.6', 'changefreq': 'monthly'},
    ]
    
    for page in static_pages:
        pages.append({
            'loc': request.url_root[:-1] + page['url'],
            'lastmod': ten_days_ago,
            'changefreq': page['changefreq'],
            'priority': page['priority']
        })
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{page["loc"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-3229320652703762, DIRECT, f08c47fec0942fa0"
    response = make_response(content)
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
        if month % 12 == 0:
            values[month] *= (1 - expense_ratio)

    gross_corpus = values[-1]
    total_invested = monthly_sip * total_months

    values_no_fee = np.zeros(total_months + 1)
    for month in range(1, total_months + 1):
        values_no_fee[month] = (values_no_fee[month - 1] + monthly_sip) * (1 + monthly_return)

    corpus_no_fee = values_no_fee[-1]
    fees_paid = max(0, corpus_no_fee - gross_corpus)

    capital_gains = max(0, gross_corpus - total_invested)
    
    if years > 1:
        taxable_ltcg = max(0, capital_gains - 100000)
        capital_gains_tax = taxable_ltcg * ltcg_rate
        tax_type = "LTCG"
    else:
        capital_gains_tax = capital_gains * stcg_rate
        tax_type = "STCG"
    
    corpus_after_tax = gross_corpus - capital_gains_tax

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
    gross_corpus_no_fee = lumpsum_amount * ((1 + annual_return) ** years)
    
    gross_corpus = lumpsum_amount
    for year in range(years):
        gross_corpus *= (1 + annual_return)
        gross_corpus *= (1 - expense_ratio)
    
    fees_paid = max(0, gross_corpus_no_fee - gross_corpus)
    capital_gains = max(0, gross_corpus - lumpsum_amount)
    
    if years > 1:
        taxable_ltcg = max(0, capital_gains - 100000)
        capital_gains_tax = taxable_ltcg * ltcg_rate
        tax_type = "LTCG"
    else:
        capital_gains_tax = capital_gains * stcg_rate
        tax_type = "STCG"
    
    corpus_after_tax = gross_corpus - capital_gains_tax
    
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
    frequency_map = {
        'yearly': 1,
        'half-yearly': 2, 
        'quarterly': 4,
        'monthly': 12,
        'daily': 365
    }
    
    n = frequency_map.get(compounding_frequency, 4)
    maturity_amount = principal_amount * ((1 + annual_interest_rate / n) ** (n * years))
    interest_earned = maturity_amount - principal_amount
    effective_rate = ((maturity_amount / principal_amount) ** (1 / years) - 1) * 100
    
    return {
        "principal_amount": round(principal_amount, 2),
        "maturity_amount": round(maturity_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round(effective_rate, 2)
    }


def calculate_rd(monthly_deposit, annual_interest_rate, years, compounding_frequency):
    frequency_map = {
        'yearly': 1,
        'half-yearly': 2, 
        'quarterly': 4,
        'monthly': 12,
        'daily': 365
    }
    
    n = frequency_map.get(compounding_frequency, 4)
    total_months = years * 12
    maturity_amount = 0
    
    for month in range(1, total_months + 1):
        time_remaining = (total_months - month + 1) / 12
        if time_remaining > 0:
            deposit_maturity = monthly_deposit * ((1 + annual_interest_rate / n) ** (n * time_remaining))
            maturity_amount += deposit_maturity
        else:
            maturity_amount += monthly_deposit
    
    total_invested = monthly_deposit * total_months
    interest_earned = maturity_amount - total_invested
    effective_rate = ((maturity_amount / total_invested) ** (1 / years) - 1) * 100
    
    return {
        "monthly_deposit": round(monthly_deposit, 2),
        "total_invested": round(total_invested, 2),
        "maturity_amount": round(maturity_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round(effective_rate, 2)
    }


def calculate_swp(initial_corpus, monthly_withdrawal, annual_return, expense_ratio, inflation_rate=0):
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    
    corpus = initial_corpus
    total_withdrawn = 0
    month = 0
    monthly_withdrawals = []
    corpus_values = []
    
    current_withdrawal = monthly_withdrawal
    
    while corpus > 0 and month < 600:
        month += 1
        corpus *= (1 + monthly_return)
        
        if month % 12 == 0:
            corpus *= (1 - expense_ratio)
        
        if inflation_rate > 0 and month > 1:
            current_withdrawal *= (1 + monthly_inflation)
        
        actual_withdrawal = min(current_withdrawal, corpus)
        corpus -= actual_withdrawal
        total_withdrawn += actual_withdrawal
        
        monthly_withdrawals.append(actual_withdrawal)
        corpus_values.append(corpus)
        
        if corpus < 1:
            break
    
    avg_monthly_withdrawal = total_withdrawn / month if month > 0 else 0
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
        "monthly_withdrawals": monthly_withdrawals[:60],
        "corpus_values": corpus_values[:60]
    }


def create_pie_chart(total_invested, net_return, fees_paid, capital_gains_tax):
    labels = ['Invested Amount', 'Net Return', 'Fees', 'Capital Gains Tax']
    values = [total_invested, net_return, fees_paid, capital_gains_tax]
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
    
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
    labels = ['Total Invested', 'Net Return']
    values = [total_invested, net_return]
    colors = ['#3498db', '#2ecc71']
    
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
    months = list(range(1, len(corpus_values) + 1))
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    ax1.plot(months, corpus_values, color='#e74c3c', linewidth=2, marker='o', markersize=3)
    ax1.set_title('Corpus Value Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Months')
    ax1.set_ylabel('Corpus Value (₹)')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
    
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
    active_tab = "simple"
    calculator_type = "sip"

    if request.method == 'POST':
        form_type = request.form.get('form_type', 'advanced')
        
        if form_type == 'advanced':
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
                calculator_type = "fd"

            except Exception as e:
                print("Error:", e)

        elif form_type == 'rd':
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
                calculator_type = "rd"

            except Exception as e:
                print("Error:", e)

        elif form_type == 'swp':
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
                calculator_type = "swp"

            except Exception as e:
                print("Error:", e)
                
        elif form_type == 'simple':
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


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# Add cache control headers for better performance
@app.after_request
def add_header(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 year
    else:
        response.cache_control.no_cache = True
        response.cache_control.must_revalidate = True
    return response

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


if __name__ == '__main__':
    app.run(debug=True)
