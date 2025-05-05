from flask import Flask, render_template, request
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

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


def calculate_sip(monthly_sip, annual_return, expense_ratio, years, inflation_rate):
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

    # Post-fee corpus
    corpus_after_tax = gross_corpus-fees_paid

    # Inflation impact
    inflation_impact = max(0, corpus_after_tax * (1 - (1 / ((1 + inflation_rate) ** years))))
    final_corpus = corpus_after_tax - inflation_impact
    final_corpus = max(0, min(final_corpus, gross_corpus))

    net_return = max(0, corpus_after_tax - total_invested)

    return {
        "total_invested": round(total_invested, 2),
        "gross_corpus": round(gross_corpus, 2),
        "fees_paid": round(fees_paid, 2),
        "inflation_adjusted_final_corpus": round(final_corpus, 2),
        "final_corpus": round(corpus_after_tax, 2),
        "net_return": round(net_return, 2),
    }

def format_full_with_unit(value):
    formatted_full = f"{value:,.2f}"
    if value >= 1e7:
        unit = f"{value / 1e7:.2f} Cr"
    elif value >= 1e5:
        unit = f"{value / 1e5:.2f} Lakh"
    else:
        unit = None

    return f"{formatted_full} ({unit})" if unit else formatted_full

def create_pie_chart(total_invested, net_return, fees_paid):
    labels = ['Invested Amount', 'Net Return', 'Fees']
    values = [total_invested, net_return, fees_paid]
    colors = ['#3498db', '#2ecc71', '#e74c3c']

    plt.figure(figsize=(7, 7))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("SIP Gross Corpus Breakdown")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
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

    if request.method == 'POST':
        try:
            form_data = {
                "monthly_sip": float(request.form['monthly_sip']),
                "annual_return": float(request.form['annual_return']) / 100,
                "expense_ratio": float(request.form['expense_ratio']) / 100,
                "years": int(request.form['years']),
                "inflation_rate": float(request.form.get('inflation_rate', 0)) / 100,
            }

            result = calculate_sip(**form_data)
            chart = create_pie_chart(
                result["total_invested"],
                result["net_return"],
                result["fees_paid"]
            )

        except Exception as e:
            print("Error:", e)

    return render_template('index.html', result=result, chart=chart, form_data=form_data)


if __name__ == '__main__':
    app.run(debug=True)
