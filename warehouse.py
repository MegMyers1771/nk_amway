import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

warehouse_path = "warehouse.json"
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('nikitastorage.json', scope)
client = gspread.authorize(creds)

def load_warehouse_items():

    # Открытие листа
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/135TzPDuf6r_Bgw3Hf1N2rldaoZNecmQnEkukbl_U6WA/edit#gid=1173281585")
    worksheet = sheet.get_worksheet_by_id(1173281585)

    # Получаем все строки начиная со второй
    data = worksheet.get_all_values()[1:]  # Пропускаем заголовок

    print('warehouse called')

    items = []
    for idx, row in enumerate(data, start=2):  # начинаем с 2, т.к. строка 2 в таблице — первая с данными
        if len(row) < 6 or not row[5].strip():  # Столбец F — это row[5]
            break

        if row[0].strip():  # Название товара не пустое
            items.append({
                "name": row[0],
                "quantity": row[2],
                "price": row[4]
            })

    return items

def update_warehouse_after_invoice(invoice_items):
    """
    invoice_items: список словарей с полями "name" и "quantity" (списание)
    """

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/135TzPDuf6r_Bgw3Hf1N2rldaoZNecmQnEkukbl_U6WA/edit#gid=1173281585")
    worksheet = sheet.get_worksheet_by_id(1173281585)

    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    for idx, row in enumerate(rows, start=2):  # Начинаем с 2, потому что первая строка — заголовки
        item_name = row[0].strip()
        if not item_name:
            continue

        for item in invoice_items:
            if item["name"].strip() == item_name:
                try:
                    current_stock = int(row[2])  # Столбец "Количество на складе"
                    deduction = int(item["quantity"])
                    new_stock = max(current_stock - deduction, 0)  # Не уходим в минус
                    worksheet.update_cell(idx, 3, str(new_stock))  # Столбец C = индекс 3
                except ValueError:
                    print(f"Ошибка в числе: {row[2]} или {item['quantity']}")
                break


def dump_warehouse():
    items = load_warehouse_items()
    with open(warehouse_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

if not os.path.exists(warehouse_path):
    dump_warehouse()