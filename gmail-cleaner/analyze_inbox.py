"""
Gmail Inbox Analyzer
Анализирует все письма во входящих и выводит статистику по отправителям.
"""

import os
import re
from collections import Counter
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token_readonly.json')


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print("✅ Авторизация прошла успешно.")
    return build('gmail', 'v1', credentials=creds)


def extract_sender(from_header):
    """Извлекает email из заголовка From."""
    match = re.search(r'<(.+?)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


def extract_domain(email):
    """Извлекает домен из email."""
    if '@' in email:
        return email.split('@')[1]
    return email


def fetch_all_inbox(service):
    """Скачивает все письма из inbox (только заголовки From и Subject)."""
    messages = []
    page_token = None
    print("📥 Загружаю список писем", end='', flush=True)

    while True:
        kwargs = {
            'userId': 'me',
            'labelIds': ['INBOX'],
            'maxResults': 500,
            'fields': 'messages/id,nextPageToken'
        }
        if page_token:
            kwargs['pageToken'] = page_token

        result = service.users().messages().list(**kwargs).execute()
        batch = result.get('messages', [])
        messages.extend(batch)
        print('.', end='', flush=True)

        page_token = result.get('nextPageToken')
        if not page_token:
            break

    print(f" {len(messages)} писем")
    return messages


def fetch_headers_batch(service, message_ids):
    """Получает заголовки From и Subject для пакета писем."""
    results = []

    def callback(request_id, response, exception):
        if exception is None and response:
            headers = {h['name']: h['value'] for h in response.get('payload', {}).get('headers', [])}
            results.append({
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
            })

    batch = service.new_batch_http_request(callback=callback)
    for msg_id in message_ids:
        batch.add(service.users().messages().get(
            userId='me', id=msg_id, format='metadata',
            metadataHeaders=['From', 'Subject']
        ))
    batch.execute()
    return results


def main():
    print("=" * 60)
    print("  Gmail Inbox Analyzer")
    print("=" * 60 + "\n")

    service = get_service()
    messages = fetch_all_inbox(service)

    print(f"\n📊 Загружаю заголовки...\n")
    all_headers = []
    batch_size = 100
    for i in range(0, len(messages), batch_size):
        chunk = [m['id'] for m in messages[i:i+batch_size]]
        all_headers.extend(fetch_headers_batch(service, chunk))
        print(f"  обработано {min(i+batch_size, len(messages))}/{len(messages)}...")

    # Статистика по отправителям (email)
    sender_counter = Counter()
    domain_counter = Counter()
    for h in all_headers:
        email = extract_sender(h['from'])
        domain = extract_domain(email)
        sender_counter[email] += 1
        domain_counter[domain] += 1

    print(f"\n{'=' * 60}")
    print(f"  Топ-30 отправителей по количеству писем во входящих")
    print(f"{'=' * 60}")
    for sender, count in sender_counter.most_common(30):
        print(f"  {count:4d}  {sender}")

    print(f"\n{'=' * 60}")
    print(f"  Топ-20 доменов")
    print(f"{'=' * 60}")
    for domain, count in domain_counter.most_common(20):
        print(f"  {count:4d}  {domain}")

    # Сохраняем полный отчёт в файл
    report_path = os.path.join(os.path.dirname(__file__), 'inbox_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Всего писем во входящих: {len(all_headers)}\n\n")
        f.write("ТОП ОТПРАВИТЕЛЕЙ:\n")
        for sender, count in sender_counter.most_common(100):
            f.write(f"  {count:4d}  {sender}\n")
        f.write("\nТОП ДОМЕНОВ:\n")
        for domain, count in domain_counter.most_common(50):
            f.write(f"  {count:4d}  {domain}\n")

    print(f"\n✅ Полный отчёт сохранён: {report_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
