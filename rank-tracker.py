import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import sys

def get_key_file_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'gsc-key.json')

KEY_FILE = get_key_file_path()  # путь к JSON

def get_keywords(filename='keywords.txt'):
    if not os.path.exists(filename):
        print(f"❌ file {filename} is not found!")
        return []

    with open(filename, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]

    print(f"✅ downloaded {len(keywords)} keywords from file {filename}")
    return keywords

def get_info():
    site = input("Enter URL of your site: ")
    period = int(input("\nEnter period (number of days): "))
    keywords = []
    keywords = get_keywords()
    if not keywords:
        print("⚠️ No keywords. Put the file keywords.txt at the same folder with app")
        return

    req(site, period, keywords)

def req(site, period, keywords):
        # подключаемся к Google
        credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        service = build('searchconsole', 'v1', credentials=credentials)

        # За какой период смотрим (последние period дней)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period)

        # Собираем данные по каждому слову
        results = []
        for kw in keywords:
            print(f'Checking: {kw}...')

            # Запрос к API
            request = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query'],
                'dimensionFilterGroups': [{
                    'filters': [{
                        'dimension': 'query',
                        'operator': 'equals',
                        'expression': kw
                    }]
                }],
                'rowLimit': 1
            }
            # обработка данных
            response = service.searchanalytics().query(siteUrl=site, body=request).execute()
            rows = response.get('rows', [])
            if rows:
                r = rows[0]
                results.append({
                    'Key Word': kw,
                    'Position': round(r.get('position', 0), 1),
                    'Clicks': r.get('clicks', 0),
                    'Impressions': r.get('impressions', 0)
                })
            else:
                results.append({
                    'Key Word': kw,
                    'Position': 'Not in TOP-10',
                    'Clicks': 0,
                    'Impressions': 0
                })


        # Сохраняем в Excel
        df = pd.DataFrame(results)
        filename = f'positions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(filename, index=False)
        print(f'\n✅ Ready! File is saved!: {filename}')



get_info()
