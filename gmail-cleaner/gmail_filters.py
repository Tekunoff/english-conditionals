"""
Gmail Filters Manager
Создаёт фильтры в Gmail через API: шум уходит в архив, важное остаётся во входящих.

Требования:
  pip install google-auth google-auth-oauthlib google-api-python-client

Использование:
  1. Скачайте credentials.json из Google Cloud Console и положите рядом с этим файлом
  2. python3 gmail_filters.py
  3. При первом запуске откроется браузер для авторизации — разрешите доступ
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Права доступа: только управление настройками (не чтение писем)
SCOPES = ['https://www.googleapis.com/auth/gmail.settings.basic']

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

# ─────────────────────────────────────────────────────────────────────────────
# ФИЛЬТРЫ: письма от этих отправителей уходят в архив, минуя входящие
# ─────────────────────────────────────────────────────────────────────────────
NOISE_FILTERS = [
    # Маркетинг и рассылки от сервисов
    {"from": "mail.perplexity.ai",          "desc": "Perplexity маркетинг"},
    {"from": "noreply@mail.perplexity.ai",  "desc": "Perplexity уведомления"},
    {"from": "opros@rostelekom.ru",         "desc": "Ростелеком опросы"},
    {"from": "noreply@docker.com",          "desc": "Docker уведомления"},
    {"from": "noreply@github.com",          "desc": "GitHub уведомления"},
    {"from": "notifications@github.com",    "desc": "GitHub notifications"},
    {"from": "noreply@jira.com",            "desc": "Jira уведомления"},
    {"from": "no_reply@accounts.google.com","desc": "Google account activity"},

    # Просьбы оставить отзыв
    {"subject": "оцените качество",        "desc": "Просьбы оценить качество"},
    {"subject": "оставьте отзыв",          "desc": "Просьбы оставить отзыв"},
    {"subject": "Приглашение пройти опрос","desc": "Приглашения пройти опрос"},

    # ── Вторая волна: крупные источники шума ──────────────────────────────
    {"from": "mann-ivanov-ferber.ru",      "desc": "МИФ издательство рассылка"},
    {"from": "l-a-b-a.com",               "desc": "LABA онлайн-школа"},
    {"from": "sbermarket.ru",             "desc": "Сберmarket промо"},
    {"from": "emails.tinkoff.ru",         "desc": "Тинькофф маркетинг"},
    {"from": "intex-rus.ru",              "desc": "Intex рассылка"},
    {"from": "skillfactory.ru",           "desc": "Skillfactory онлайн-школа"},
    {"from": "italki.com",               "desc": "iTalki маркетинг"},
    {"from": "tjournal.ru",              "desc": "TJournal дайджесты"},
    {"from": "pmbasics101.com",           "desc": "PM Basics newsletter"},
    {"from": "promo.elsanow.io",          "desc": "Elsa промо"},
    {"from": "medium.com",               "desc": "Medium дайджесты"},
    {"from": "career.habr.com",           "desc": "Хабр Карьера вакансии"},
    {"from": "aviasales.ru",             "desc": "Авиасейлс промо"},
    {"from": "zerofasting.com",           "desc": "Zero Fasting маркетинг"},
    {"from": "beelinguapp.com",           "desc": "Beelingu маркетинг"},
    {"from": "fl.ru",                    "desc": "FL.ru рассылка"},
    {"from": "borisbilet.com",            "desc": "Борис Билет промо"},
    {"from": "domclick.ru",              "desc": "Домклик маркетинг"},

    # ── Третья волна ──────────────────────────────────────────────────────────
    {"from": "notifications@avito.ru",      "desc": "Авито промо"},
    {"from": "bonus@bns-group.ru",          "desc": "BNS Group бонусы"},
    {"from": "mail.epicvin.com",            "desc": "EpicVin рассылка"},
    {"from": "noreply@glassdoor.com",       "desc": "Glassdoor вакансии"},
    {"from": "news.nianticlabs.com",        "desc": "Niantic / Pokemon Go"},
    {"from": "info.rt.ru",                  "desc": "Ростелеком info рассылка"},
    {"from": "smfd.rt.ru",                  "desc": "Ростелеком smfd рассылка"},
    {"from": "ural.rt.ru",                  "desc": "Ростелеком ural рассылка"},
    {"from": "promo@privetmir.ru",          "desc": "Привет Мир промо"},
    {"from": "noreply@pizzahut.ru",         "desc": "Pizza Hut промо"},
    {"from": "contact@antirabstvo.ru",      "desc": "Антирабство newsletter"},
    {"from": "noreply@mail.restore.ru",     "desc": "Restore рассылка"},
    {"from": "quora.com",                   "desc": "Quora дайджесты"},
    {"from": "sender.mvideo.ru",            "desc": "М.Видео промо"},
    {"from": "mail.surfshark.com",          "desc": "Surfshark промо"},
    {"from": "notify.ivi.ru",               "desc": "IVI промо"},
    {"from": "emails.tinkoffinsurance.ru",  "desc": "Тинькофф Страхование"},
    {"from": "news@stoplight.io",           "desc": "Stoplight newsletter"},
    {"from": "event@picom.ru",              "desc": "Picom промо"},
    {"from": "manager@skillum.com",         "desc": "Skillum онлайн-школа"},
    {"from": "5post@x5.ru",                "desc": "X5 промо"},
    {"from": "noreply@paygine.net",         "desc": "Paygine уведомления"},
    {"from": "noreply@steampowered.com",    "desc": "Steam уведомления"},
    {"from": "support@yclients.com",        "desc": "YClients рассылка"},

    # ── Четвёртая волна ──────────────────────────────────────────────────────
    {"from": "unipen.ru",                    "desc": "Unipen интернет-магазин"},
    {"from": "kantslyudi.ru",               "desc": "Канцлюди рассылка"},
    {"from": "pb01.ascendbywix.com",        "desc": "Wix спам-рассылка"},
    {"from": "noreply@vc.ru",               "desc": "VC.ru дайджесты"},
    {"from": "no-reply@spotify.com",        "desc": "Spotify промо"},
    {"from": "netology.ru",                 "desc": "Нетология рассылка"},
    {"from": "laba.academy",               "desc": "LABA academy рассылка"},
    {"from": "allsoft.ru",                  "desc": "Allsoft/Kaspersky промо"},
    {"from": "noreply@aerisweather.com",    "desc": "AerisWeather уведомления"},
    {"from": "noreply@x.ai",               "desc": "xAI/Grok рассылка"},
    {"from": "mubert.com",                 "desc": "Mubert промо"},
    {"from": "rus.vote",                   "desc": "rus.vote рассылка"},
    {"from": "noreply@skyslope.com",        "desc": "Skyslope рассылка"},
    {"from": "eccorek@e-izhevsk.ru",        "desc": "e-izhevsk рассылка"},
    {"from": "support@perplexity.ai",       "desc": "Perplexity support рассылка"},
    {"from": "assistant@perplexity.com",    "desc": "Perplexity assistant рассылка"},

    # ── Пятая волна (финальная) ─────────────────────────────────────────────
    {"from": "notify.docker.com",            "desc": "Docker notify поддомен"},
    {"from": "mubi.com",                     "desc": "MUBI промо"},
    {"from": "team@vpn-naruzhu.com",         "desc": "VPN рассылка"},
    {"from": "school.skysmart.ru",           "desc": "Skysmart онлайн-школа"},
    {"from": "engage.wordtune.com",          "desc": "Wordtune промо"},
    {"from": "subs@svyaznoy.ru",             "desc": "Связной промо"},
    {"from": "leroymerlin.ru",              "desc": "Леруа Мерлен промо"},
    {"from": "apteka.ru",                   "desc": "Аптека.ру промо"},
    {"from": "updates.truecaller.com",      "desc": "Truecaller промо"},
    {"from": "email.withings.com",          "desc": "Withings рассылка"},
    {"from": "updates.meditopia.com",       "desc": "Meditopia промо"},
    {"from": "info@onebook.ru",             "desc": "OneBook рассылка"},
    {"from": "trustpilotmail.com",          "desc": "Trustpilot отзывы"},
    {"from": "t.mail.coursera.org",         "desc": "Coursera промо"},
    {"from": "decathlon.com",               "desc": "Декатлон промо"},
    {"from": "it.agent@autodoc.ru",         "desc": "AutoDoc промо"},
    {"from": "crm@talan.group",             "desc": "Талан маркетинг"},
    {"from": "noreply@mail.vc.ru",          "desc": "VC.ru поддомен"},
    {"from": "no-reply@ypmn.ru",            "desc": "YPMN рассылка"},
    {"from": "oy.lazareva@uds18.ru",        "desc": "UDS18 рассылка"},
    {"from": "lipinanot@mail.ru",           "desc": "lipinanot рассылка"},
    {"from": "support@gkeys24.com",         "desc": "GKeys24 рассылка"},
    {"from": "info@bankoff.co",             "desc": "Bankoff рассылка"},
    {"from": "info@alfastrahmail.ru",       "desc": "Альфастрахование рассылка"},
    {"from": "alena@vladimirskaya.com",     "desc": "vladimirskaya.com рассылка"},
    {"from": "uicdev@mediator.cloud",       "desc": "Mediator Cloud рассылка"},
    {"from": "region.invest.18@gmail.com",  "desc": "region.invest.18 рассылка"},
    {"from": "no-reply@todoist.com",        "desc": "Todoist уведомления"},
    {"from": "info@privetmir.ru",           "desc": "Привет Мир info"},
    {"from": "welovenocode.com",            "desc": "WelovNoCode рассылка"},
    {"from": "noreply@nsis.ru",             "desc": "NSIS рассылка"},
    {"from": "help.elsanow.io",             "desc": "Elsa help поддомен"},
    {"from": "info.n8n.io",                "desc": "n8n newsletter"},
    {"from": "aigtravel.com",               "desc": "AIG Travel промо"},
    {"from": "no-reply@chaos.com",          "desc": "Chaos Group промо"},
    {"from": "no-reply@chaosgroup.com",     "desc": "ChaosGroup промо"},
    {"from": "sendbox@htmlacademy.ru",      "desc": "HTML Academy рассылка"},
    {"from": "newsletters@e.couponfollow.com","desc": "CouponFollow спам"},
    {"from": "news@elma-bpm.ru",            "desc": "ELMA BPM рассылка"},
    {"from": "events@tceh.com",             "desc": "TCEH рассылка"},
    {"from": "infoclub@mexicodestinationclub.com","desc": "Mexico Club спам"},
    {"from": "noreply@bmwgroup.com",        "desc": "BMW Group промо"},
    {"from": "info@pro.mubert.com",         "desc": "Mubert pro поддомен"},

    # ── Шестая волна ──────────────────────────────────────────────────────
    {"from": "shoes.kari.com",              "desc": "KARI обувь"},
    {"from": "emails.brooksbrothers.com",   "desc": "Brooks Brothers промо"},
    {"from": "official.nike.com",           "desc": "Nike промо"},
    {"from": "customer@eldorado.ru",        "desc": "Эльдорадо промо"},
    {"from": "subscribe@tinkoffjournal.ru", "desc": "Тинькофф Журнал"},
    {"from": "info@lingualeo.com",          "desc": "LinguaLeo рассылка"},
    {"from": "mailer@market.yandex.ru",     "desc": "Яндекс Маркет промо"},
    {"from": "adl.skyeng.ru",              "desc": "SkyEng рассылка"},
    {"from": "info@danceplus.com",          "desc": "DancePlus рассылка"},
    {"from": "noreplay@kinoteatr.ru",       "desc": "Кинотеатр.ру"},
    {"from": "noreply@lingbase.com",        "desc": "Lingbase рассылка"},
    {"from": "noreply@tracktest.eu",        "desc": "TrackTest рассылка"},
    {"from": "promo@bronevik.com",          "desc": "Bronevik промо"},
    {"from": "info@services.teamviewer.com","desc": "TeamViewer рассылка"},
    {"from": "team@comms.evernote.com",     "desc": "Evernote рассылка"},
    {"from": "email.coursera.org",          "desc": "Coursera поддомен"},
    {"from": "info.surfshark.com",          "desc": "Surfshark поддомен"},
    {"from": "noreply@elma-bpm.ru",         "desc": "ELMA BPM поддомен"},
    {"from": "support@m-i-f.ru",            "desc": "МИФ m-i-f.ru"},
    {"from": "info@kcentr.ru",             "desc": "kcentr.ru рассылка"},
    {"from": "mail.salebot.pro",           "desc": "Salebot рассылка"},
    {"from": "downdogapp.com",             "desc": "Down Dog app"},
    {"from": "info@cherehapa.ru",           "desc": "Черехапа страховки"},
    {"from": "service@notice.alibaba.com",  "desc": "Alibaba рассылка"},
    {"from": "korepanovaoa@vtb.ru",         "desc": "ВТБ маркетинг"},
    {"from": "noreply@sirena-travel.ru",    "desc": "Сирена Travel"},
    {"from": "notification@miro.com",       "desc": "Miro уведомления"},
    {"from": "notifications@discord.com",   "desc": "Discord уведомления"},
    {"from": "make.com",                   "desc": "Make.com рассылка"},
    {"from": "noreply@majid-al-futtaim.contact-mailer.com","desc": "Majid Al Futtaim промо"},
    {"from": "order@iphoster.net",           "desc": "IPhoster маркетинг"},
]


def get_service():
    """Авторизация и создание Gmail API клиента."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"\n❌ Файл {CREDENTIALS_FILE} не найден!")
                print("   Скачайте его из Google Cloud Console:")
                print("   APIs & Services → Credentials → OAuth 2.0 Clients → скачать JSON")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("✅ Авторизация прошла успешно, токен сохранён.")

    return build('gmail', 'v1', credentials=creds)


def get_existing_filters(service):
    """Получить список существующих фильтров."""
    result = service.users().settings().filters().list(userId='me').execute()
    return result.get('filter', [])


def create_filter(service, criteria: dict, desc: str):
    """Создать один фильтр: пропустить входящие + пометить как прочитанное."""
    filter_body = {
        "criteria": criteria,
        "action": {
            "removeLabelIds": ["INBOX"],   # убрать из входящих (архивировать)
        }
    }
    try:
        result = service.users().settings().filters().create(
            userId='me', body=filter_body
        ).execute()
        print(f"  ✅ Создан: {desc}  (id: {result.get('id')})")
        return result
    except Exception as e:
        print(f"  ⚠️  Ошибка для '{desc}': {e}")
        return None


def main():
    print("=" * 60)
    print("  Gmail Filters Manager")
    print("=" * 60)

    service = get_service()

    existing = get_existing_filters(service)
    print(f"\n📋 Найдено существующих фильтров: {len(existing)}")

    # Собираем множество уже существующих критериев для быстрой проверки дублей
    existing_criteria = set()
    for ef in existing:
        c = ef.get('criteria', {})
        existing_criteria.add(frozenset(c.items()))

    to_create = []
    for f in NOISE_FILTERS:
        desc = f.pop("desc")
        key = frozenset(f.items())
        if key in existing_criteria:
            f['desc'] = desc  # вернуть desc обратно для следующих запусков
            continue
        to_create.append((f, desc))

    print(f"\n🚀 Создаю {len(to_create)} новых фильтров (пропущено {len(NOISE_FILTERS) - len(to_create)} существующих)...\n")
    created = 0

    for criteria, desc in to_create:
        result = create_filter(service, criteria, desc)
        if result:
            created += 1

    print(f"\n{'=' * 60}")
    print(f"  Готово! Создано фильтров: {created} из {len(to_create)}")
    print(f"  Все письма от шумных отправителей теперь обходят входящие.")
    print("=" * 60)


if __name__ == '__main__':
    main()
