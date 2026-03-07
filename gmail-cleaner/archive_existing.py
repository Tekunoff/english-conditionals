"""
Gmail Archive Existing
Архивирует уже существующие письма от шумных отправителей.

Запуск:
  python3 archive_existing.py
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Расширенный scope — нужен для чтения и изменения писем
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token_modify.json')

# ─────────────────────────────────────────────────────────────────────────────
# Поисковые запросы для архивации существующих писем
# Формат Gmail search: те же операторы, что в строке поиска Gmail
# ─────────────────────────────────────────────────────────────────────────────
ARCHIVE_QUERIES = [
    {"query": "from:mail.perplexity.ai in:inbox",           "desc": "Perplexity"},
    {"query": "from:noreply@mail.perplexity.ai in:inbox",   "desc": "Perplexity noreply"},
    {"query": "from:opros@rostelekom.ru in:inbox",          "desc": "Ростелеком опросы"},
    {"query": "from:noreply@docker.com in:inbox",           "desc": "Docker"},
    {"query": "from:noreply@github.com in:inbox",           "desc": "GitHub noreply"},
    {"query": "from:notifications@github.com in:inbox",     "desc": "GitHub notifications"},
    {"query": "from:noreply@jira.com in:inbox",             "desc": "Jira"},
    {"query": "from:no_reply@accounts.google.com in:inbox", "desc": "Google account activity"},
    {"query": "subject:(оцените качество) in:inbox",        "desc": "Оценка качества"},
    {"query": "subject:(оставьте отзыв) in:inbox",          "desc": "Просьбы отзыв"},
    {"query": "subject:(Приглашение пройти опрос) in:inbox","desc": "Опросы"},

    # ── Вторая волна ──────────────────────────────────────────────────────
    {"query": "from:mann-ivanov-ferber.ru in:inbox",      "desc": "МИФ издательство"},
    {"query": "from:l-a-b-a.com in:inbox",               "desc": "LABA онлайн-школа"},
    {"query": "from:sbermarket.ru in:inbox",             "desc": "Сберmarket промо"},
    {"query": "from:emails.tinkoff.ru in:inbox",         "desc": "Тинькофф маркетинг"},
    {"query": "from:intex-rus.ru in:inbox",              "desc": "Intex рассылка"},
    {"query": "from:skillfactory.ru in:inbox",           "desc": "Skillfactory"},
    {"query": "from:italki.com in:inbox",               "desc": "iTalki маркетинг"},
    {"query": "from:tjournal.ru in:inbox",              "desc": "TJournal дайджесты"},
    {"query": "from:pmbasics101.com in:inbox",           "desc": "PM Basics newsletter"},
    {"query": "from:promo.elsanow.io in:inbox",          "desc": "Elsa промо"},
    {"query": "from:medium.com in:inbox",               "desc": "Medium дайджесты"},
    {"query": "from:career.habr.com in:inbox",           "desc": "Хабр Карьера"},
    {"query": "from:aviasales.ru in:inbox",             "desc": "Авиасейлс промо"},
    {"query": "from:zerofasting.com in:inbox",           "desc": "Zero Fasting"},
    {"query": "from:beelinguapp.com in:inbox",           "desc": "Beelingu маркетинг"},
    {"query": "from:fl.ru in:inbox",                    "desc": "FL.ru рассылка"},
    {"query": "from:borisbilet.com in:inbox",            "desc": "Борис Билет промо"},
    {"query": "from:domclick.ru in:inbox",              "desc": "Домклик маркетинг"},

    # ── Третья волна ──────────────────────────────────────────────────────────
    {"query": "from:notifications@avito.ru in:inbox",      "desc": "Авито промо"},
    {"query": "from:bonus@bns-group.ru in:inbox",          "desc": "BNS Group бонусы"},
    {"query": "from:mail.epicvin.com in:inbox",            "desc": "EpicVin рассылка"},
    {"query": "from:noreply@glassdoor.com in:inbox",       "desc": "Glassdoor вакансии"},
    {"query": "from:news.nianticlabs.com in:inbox",        "desc": "Niantic / Pokemon Go"},
    {"query": "from:info.rt.ru in:inbox",                  "desc": "Ростелеком info"},
    {"query": "from:smfd.rt.ru in:inbox",                  "desc": "Ростелеком smfd"},
    {"query": "from:ural.rt.ru in:inbox",                  "desc": "Ростелеком ural"},
    {"query": "from:promo@privetmir.ru in:inbox",          "desc": "Привет Мир промо"},
    {"query": "from:noreply@pizzahut.ru in:inbox",         "desc": "Pizza Hut промо"},
    {"query": "from:contact@antirabstvo.ru in:inbox",      "desc": "Антирабство"},
    {"query": "from:noreply@mail.restore.ru in:inbox",     "desc": "Restore рассылка"},
    {"query": "from:quora.com in:inbox",                   "desc": "Quora дайджесты"},
    {"query": "from:sender.mvideo.ru in:inbox",            "desc": "М.Видео промо"},
    {"query": "from:mail.surfshark.com in:inbox",          "desc": "Surfshark промо"},
    {"query": "from:notify.ivi.ru in:inbox",               "desc": "IVI промо"},
    {"query": "from:emails.tinkoffinsurance.ru in:inbox",  "desc": "Тинькофф Страхование"},
    {"query": "from:news@stoplight.io in:inbox",           "desc": "Stoplight newsletter"},
    {"query": "from:event@picom.ru in:inbox",              "desc": "Picom промо"},
    {"query": "from:manager@skillum.com in:inbox",         "desc": "Skillum"},
    {"query": "from:5post@x5.ru in:inbox",                "desc": "X5 промо"},
    {"query": "from:noreply@paygine.net in:inbox",         "desc": "Paygine"},
    {"query": "from:noreply@steampowered.com in:inbox",    "desc": "Steam"},
    {"query": "from:support@yclients.com in:inbox",        "desc": "YClients"},

    # ── Четвёртая волна ──────────────────────────────────────────────────────
    {"query": "from:unipen.ru in:inbox",                    "desc": "Unipen"},
    {"query": "from:kantslyudi.ru in:inbox",               "desc": "Канцлюди"},
    {"query": "from:pb01.ascendbywix.com in:inbox",        "desc": "Wix спам"},
    {"query": "from:noreply@vc.ru in:inbox",               "desc": "VC.ru дайджесты"},
    {"query": "from:no-reply@spotify.com in:inbox",        "desc": "Spotify промо"},
    {"query": "from:netology.ru in:inbox",                 "desc": "Нетология"},
    {"query": "from:laba.academy in:inbox",               "desc": "LABA academy"},
    {"query": "from:allsoft.ru in:inbox",                  "desc": "Allsoft"},
    {"query": "from:noreply@aerisweather.com in:inbox",    "desc": "AerisWeather"},
    {"query": "from:noreply@x.ai in:inbox",               "desc": "xAI/Grok"},
    {"query": "from:mubert.com in:inbox",                 "desc": "Mubert"},
    {"query": "from:rus.vote in:inbox",                   "desc": "rus.vote"},
    {"query": "from:noreply@skyslope.com in:inbox",        "desc": "Skyslope"},
    {"query": "from:eccorek@e-izhevsk.ru in:inbox",        "desc": "e-izhevsk"},
    {"query": "from:support@perplexity.ai in:inbox",       "desc": "Perplexity support"},
    {"query": "from:assistant@perplexity.com in:inbox",    "desc": "Perplexity assistant"},

    # ── Пятая волна (финальная) ─────────────────────────────────────────────
    {"query": "from:notify.docker.com in:inbox",            "desc": "Docker notify"},
    {"query": "from:mubi.com in:inbox",                     "desc": "MUBI промо"},
    {"query": "from:team@vpn-naruzhu.com in:inbox",         "desc": "VPN рассылка"},
    {"query": "from:school.skysmart.ru in:inbox",           "desc": "Skysmart"},
    {"query": "from:engage.wordtune.com in:inbox",          "desc": "Wordtune"},
    {"query": "from:subs@svyaznoy.ru in:inbox",             "desc": "Связной промо"},
    {"query": "from:leroymerlin.ru in:inbox",              "desc": "Леруа Мерлен"},
    {"query": "from:apteka.ru in:inbox",                   "desc": "Аптека.ру"},
    {"query": "from:updates.truecaller.com in:inbox",      "desc": "Truecaller"},
    {"query": "from:email.withings.com in:inbox",          "desc": "Withings"},
    {"query": "from:updates.meditopia.com in:inbox",       "desc": "Meditopia"},
    {"query": "from:info@onebook.ru in:inbox",             "desc": "OneBook"},
    {"query": "from:trustpilotmail.com in:inbox",          "desc": "Trustpilot"},
    {"query": "from:t.mail.coursera.org in:inbox",         "desc": "Coursera"},
    {"query": "from:decathlon.com in:inbox",               "desc": "Декатлон"},
    {"query": "from:it.agent@autodoc.ru in:inbox",         "desc": "AutoDoc"},
    {"query": "from:crm@talan.group in:inbox",             "desc": "Талан"},
    {"query": "from:noreply@mail.vc.ru in:inbox",          "desc": "VC.ru поддомен"},
    {"query": "from:no-reply@ypmn.ru in:inbox",            "desc": "YPMN"},
    {"query": "from:oy.lazareva@uds18.ru in:inbox",        "desc": "UDS18"},
    {"query": "from:lipinanot@mail.ru in:inbox",           "desc": "lipinanot"},
    {"query": "from:support@gkeys24.com in:inbox",         "desc": "GKeys24"},
    {"query": "from:info@bankoff.co in:inbox",             "desc": "Bankoff"},
    {"query": "from:info@alfastrahmail.ru in:inbox",       "desc": "Альфастрах"},
    {"query": "from:alena@vladimirskaya.com in:inbox",     "desc": "vladimirskaya.com"},
    {"query": "from:uicdev@mediator.cloud in:inbox",       "desc": "Mediator Cloud"},
    {"query": "from:region.invest.18@gmail.com in:inbox",  "desc": "region.invest.18"},
    {"query": "from:no-reply@todoist.com in:inbox",        "desc": "Todoist"},
    {"query": "from:info@privetmir.ru in:inbox",           "desc": "Привет Мир info"},
    {"query": "from:welovenocode.com in:inbox",            "desc": "WelovNoCode"},
    {"query": "from:noreply@nsis.ru in:inbox",             "desc": "NSIS"},
    {"query": "from:help.elsanow.io in:inbox",             "desc": "Elsa help"},
    {"query": "from:info.n8n.io in:inbox",                "desc": "n8n"},
    {"query": "from:aigtravel.com in:inbox",               "desc": "AIG Travel"},
    {"query": "from:no-reply@chaos.com in:inbox",          "desc": "Chaos Group"},
    {"query": "from:no-reply@chaosgroup.com in:inbox",     "desc": "ChaosGroup"},
    {"query": "from:sendbox@htmlacademy.ru in:inbox",      "desc": "HTML Academy"},
    {"query": "from:newsletters@e.couponfollow.com in:inbox","desc": "CouponFollow"},
    {"query": "from:news@elma-bpm.ru in:inbox",            "desc": "ELMA BPM"},
    {"query": "from:events@tceh.com in:inbox",             "desc": "TCEH"},
    {"query": "from:infoclub@mexicodestinationclub.com in:inbox","desc": "Mexico Club"},
    {"query": "from:noreply@bmwgroup.com in:inbox",        "desc": "BMW Group"},
    {"query": "from:info@pro.mubert.com in:inbox",         "desc": "Mubert pro"},

    # ── Шестая волна ──────────────────────────────────────────────────────
    {"query": "from:shoes.kari.com in:inbox",              "desc": "KARI"},
    {"query": "from:emails.brooksbrothers.com in:inbox",   "desc": "Brooks Brothers"},
    {"query": "from:official.nike.com in:inbox",           "desc": "Nike"},
    {"query": "from:customer@eldorado.ru in:inbox",        "desc": "Эльдорадо"},
    {"query": "from:subscribe@tinkoffjournal.ru in:inbox", "desc": "Тинькофф Журнал"},
    {"query": "from:info@lingualeo.com in:inbox",          "desc": "LinguaLeo"},
    {"query": "from:mailer@market.yandex.ru in:inbox",     "desc": "Яндекс Маркет"},
    {"query": "from:adl.skyeng.ru in:inbox",              "desc": "SkyEng"},
    {"query": "from:info@danceplus.com in:inbox",          "desc": "DancePlus"},
    {"query": "from:noreplay@kinoteatr.ru in:inbox",       "desc": "Кинотеатр"},
    {"query": "from:noreply@lingbase.com in:inbox",        "desc": "Lingbase"},
    {"query": "from:noreply@tracktest.eu in:inbox",        "desc": "TrackTest"},
    {"query": "from:promo@bronevik.com in:inbox",          "desc": "Bronevik"},
    {"query": "from:info@services.teamviewer.com in:inbox","desc": "TeamViewer"},
    {"query": "from:team@comms.evernote.com in:inbox",     "desc": "Evernote"},
    {"query": "from:email.coursera.org in:inbox",          "desc": "Coursera поддомен"},
    {"query": "from:info.surfshark.com in:inbox",          "desc": "Surfshark поддомен"},
    {"query": "from:noreply@elma-bpm.ru in:inbox",         "desc": "ELMA BPM поддомен"},
    {"query": "from:support@m-i-f.ru in:inbox",            "desc": "МИФ m-i-f.ru"},
    {"query": "from:info@kcentr.ru in:inbox",             "desc": "kcentr.ru"},
    {"query": "from:mail.salebot.pro in:inbox",           "desc": "Salebot"},
    {"query": "from:downdogapp.com in:inbox",             "desc": "Down Dog"},
    {"query": "from:info@cherehapa.ru in:inbox",           "desc": "Черехапа"},
    {"query": "from:service@notice.alibaba.com in:inbox",  "desc": "Alibaba"},
    {"query": "from:korepanovaoa@vtb.ru in:inbox",         "desc": "ВТБ"},
    {"query": "from:noreply@sirena-travel.ru in:inbox",    "desc": "Сирена Travel"},
    {"query": "from:notification@miro.com in:inbox",       "desc": "Miro"},
    {"query": "from:notifications@discord.com in:inbox",   "desc": "Discord"},
    {"query": "from:make.com in:inbox",                   "desc": "Make.com"},
    {"query": "from:majid-al-futtaim.contact-mailer.com in:inbox","desc": "Majid Al Futtaim"},
    {"query": "from:order@iphoster.net in:inbox",           "desc": "IPhoster маркетинг"},
]


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


def archive_messages(service, query, desc):
    """Находит все письма по запросу и архивирует их."""
    archived = 0
    page_token = None

    while True:
        kwargs = {'userId': 'me', 'q': query, 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token

        result = service.users().messages().list(**kwargs).execute()
        messages = result.get('messages', [])

        if not messages:
            break

        # Пакетное удаление метки INBOX
        ids = [m['id'] for m in messages]
        service.users().messages().batchModify(
            userId='me',
            body={'removeLabelIds': ['INBOX'], 'ids': ids}
        ).execute()
        archived += len(ids)

        page_token = result.get('nextPageToken')
        if not page_token:
            break

    return archived


def main():
    print("=" * 60)
    print("  Gmail Archive Existing Emails")
    print("=" * 60)

    service = get_service()

    total = 0
    print(f"\n🗂  Архивирую существующие письма...\n")

    for item in ARCHIVE_QUERIES:
        count = archive_messages(service, item['query'], item['desc'])
        if count > 0:
            print(f"  ✅ {item['desc']}: архивировано {count} писем")
        else:
            print(f"  —  {item['desc']}: не найдено")
        total += count

    print(f"\n{'=' * 60}")
    print(f"  Готово! Всего архивировано: {total} писем")
    print("=" * 60)


if __name__ == '__main__':
    main()
