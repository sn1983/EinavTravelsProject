import os
from amadeus import Client, ResponseError
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # טוען את קובץ .env

# הגדרות (רצוי להשתמש ב-Environment Variables)
AMADEUS_KEY = os.getenv("AMADEUS_KEY")
AMADEUS_SECRET = os.getenv("AMADEUS_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
print("KEY:", AMADEUS_KEY)
print("SECRET:", AMADEUS_SECRET)

def format_date(date_str):
    """הופך תאריך מ-YYYY-MM-DD ל-DD/MM/YYYY"""
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')


def generate_booking_link(dest_code, dep_date, ret_date):
    """יוצר קישור חיפוש ב-Google Flights עם הרכב הנוסעים המדויק"""
    # מבנה הקישור של גוגל פלייטס (חיפוש מובנה)
    base_url = "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA0LTE2agwIAxIIL20vMDhicTlyHhIKMjAyNi0wNC0zMHIMCAMSCC9tLzA0dzI1UAGCAQsI____________AUABSAGYAQE"

    # דרך פשוטה יותר ליצור קישור חיפוש גמיש:
    link = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest_code}%20from%20TLV%20on%20{dep_date}%20through%20{ret_date}%20with%203%20adults%201%20infant"
    return link

def check_flights():
    amadeus = Client(client_id=AMADEUS_KEY, client_secret=AMADEUS_SECRET)

    destinations = [
        {"name": "תאילנד (BKK)", "code": "BKK"},
        {"name": "מיאמי (MIA)", "code": "MIA"}
    ]

    # הגדרת התאריכים (הלוך וחזור)
    dep_date = '2026-04-16'
    ret_date = '2026-04-30'

    msg = "✈️ *סוכן הטיסות: עדכון הלוך-חזור*\n"
    msg += f"👨‍👩‍👧‍👦 הרכב: 3 מבוגרים + תינוק\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"

    for dest in destinations:
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode='TLV',
                destinationLocationCode=dest['code'],
                departureDate=dep_date,
                returnDate=ret_date,
                adults=3,
                infants=1,
                currencyCode='USD',
                max=1
            )

            if response.data:
                flight = response.data[0]
                total_price = flight['price']['total']
                airline = flight['validatingAirlineCodes'][0]

                # שליפת התאריכים המדויקים מהכרטיס שנמצא
                actual_dep = flight['itineraries'][0]['segments'][0]['departure']['at'].split('T')[0]
                actual_ret = flight['itineraries'][1]['segments'][0]['departure']['at'].split('T')[0]
                booking_url = generate_booking_link(dest['code'], dep_date, ret_date)
                msg += f"📍 *{dest['name']}*\n"
                msg += f"💰 מחיר כולל: *${total_price}*\n"
                msg += f"🏢 חברה: {airline}\n"
                msg += f"🛫 יציאה: {format_date(actual_dep)}\n"
                msg += f"🛬 חזרה: {format_date(actual_ret)}\n"
                msg += f"🔗 [לחץ כאן לצפייה והזמנה ב-Google Flights]({booking_url})\n"
                msg += "────────────────\n"

                msg += "────────────────\n"
            else:
                msg += f"📍 *{dest['name']}*\n❌ לא נמצאו טיסות בתאריכים אלו.\n"
                msg += "────────────────\n"

        except ResponseError as error:
            msg += f"⚠️ שגיאה ב-{dest['name']}: {error}\n"

    # שליחת ההודעה לטלגרם
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})


if __name__ == "__main__":
    check_flights()