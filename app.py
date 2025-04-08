from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
import tempfile
import os
import json
import subprocess
from warehouse import load_warehouse_items, update_warehouse_after_invoice
from aio import process_invoice_template  # Импортируем твою функцию

app = Flask(__name__)

SETTINGS_FILE = "settings.json"

def convert_xlsx_to_pdf(xlsx_path: str):
    # Путь для временного файла PDF
    pdf_path = xlsx_path.replace(".xlsx", ".pdf")

    # Используем LibreOffice для конвертации XLSX в PDF
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", xlsx_path, '--outdir', '/tmp'])
    
    return pdf_path


@app.route("/update_warehouse")
def update_warehouse():
    items = load_warehouse_items()
    with open("warehouse.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print('good goood')
    return "OK"

@app.route("/warehouse")
def warehouse():
    with open("warehouse.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "invoice_number": 1,
        "manager": "Иванов И.И.",
        "buyer": "ООО Покупатель",
        "address": "г. Москва, ул. Примерная, д. 5",
        "payment_method": "Наличный расчет",
        "date": datetime.now().strftime("%Y-%m-%d")
    }

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET", "POST"])
def form():
    settings = load_settings()

    if request.method == "POST":
        invoice_number = int(request.form.get("invoice_number", 1))
        date = request.form.get("date")
        manager = request.form.get("manager")
        buyer = request.form.get("buyer")
        address = request.form.get("address")
        payment_method = request.form.get("payment_method")

        # Обновляем и сохраняем настройки
        settings = {
            "invoice_number": invoice_number,
            "date": date,
            "manager": manager,
            "buyer": buyer,
            "address": address,
            "payment_method": payment_method,
        }
        save_settings(settings)

        # Собираем товары
        items = []
        articles = request.form.getlist("article")
        names = request.form.getlist("name")
        quantities = request.form.getlist("quantity")
        prices = request.form.getlist("price")

        for art, name, qty, price in zip(articles, names, quantities, prices):
            if any([i != "" for i in [art, name, qty, price]]):
                items.append({
                    "article": art,
                    "name": name,
                    "quantity": float(qty),
                    "price": float(price),
                })

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            output_path = tmp.name


        year, month, day = date.split('-')

        new_date = '.'.join([day, month, year])

        process_invoice_template(
            template_path="main_template.xlsx",
            output_path=output_path,
            items=items,
            invoice_number=invoice_number,
            date=new_date,
            manager=manager,
            buyer=buyer,
            address=address,
            payment_method=payment_method,
        )

        update_warehouse_after_invoice(items)

        pdf_path = convert_xlsx_to_pdf(output_path)

        return send_file(pdf_path, as_attachment=True, download_name=f"am_nakladnaya_{new_date}.pdf")

    return render_template("form.html", settings=settings)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    # app.run(debug=True)
