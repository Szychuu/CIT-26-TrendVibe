import pandas as pd
import json
import os
import re
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"


def extract_data_with_llm(message, retries=3):
    sys_instr = "Jesteś analitykiem BOK. Wyciągasz dane do JSON."

    prompt = f"""
    Przeanalizuj wiadomość i zwróć JSON:
    {{
        "powod_zwrotu": "Uszkodzenie" | "Zły Rozmiar" | "Opóźnienie w Dostawie" | "Inne",
        "ocena": liczba 1-5,
        "zadanie": "Zwrot Środków" | "Wymiana" | "Brak Sprecyzowania"
    }}
    Wiadomość: "{message}"
    """

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instr,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"  [!] Błąd (próba {attempt + 1}): {e}")
            time.sleep(1)

    return {"powod_zwrotu": "Inne", "ocena": 3, "zadanie": "Brak Sprecyzowania"}


def generate_response_email(status, reason, rating, retries=2):
    sys_instr = "Jesteś uprzejmym asystentem Biura Obsługi Klienta sklepu internetowego TrendVibe."
    prompt = f"Napisz krótki email. Status: {status}, Powód zgłoszenia: {reason}, Zadowolenie klienta (ocena): {rating}/5. " \
             f"ZASADY: 1. Nie podawaj w treści e-maila liczbowej wartości oceny ({rating}). " \
             f"2. Dostosuj ton: jeśli ocena jest niska, bądź bardziej przepraszający. Jeśli wysoka, bądź entuzjastyczny. " \
             f"3. Podpisz się jako Zespół Obsługi Klienta."


    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instr,
                    temperature=0.6
                )
            )
            return response.text.strip()
        except Exception as e:
            time.sleep(1)

    return "Twoje zgłoszenie zostało przyjęte. Skontaktujemy się wkrótce."


def main():
    print(f"🚀 Uruchamiamy Sprytne Zwroty AI")

    try:
        zgloszenia = pd.read_csv("assets/zgloszenia_BOK.csv")
        klienci = pd.read_csv("assets/klienci_historia.csv")
        produkty = pd.read_csv("assets/katalog_produktow.csv")
    except Exception as e:
        print(f"Błąd plików: {e}")
        return

    zgloszenia['CREATED_AT'] = pd.to_datetime(zgloszenia['CREATED_AT'])
    zgloszenia = zgloszenia.sort_values(by='CREATED_AT', ascending=True)
    df = zgloszenia.merge(klienci, on="CUSTOMER_ID", how="left").merge(produkty, on="PRODUCT_ID", how="left")

    raport_automatyczny = []
    do_recznej_weryfikacji = []
    legal_pattern = re.compile(r'\b(prawnik\w*|uokik|sąd\w*|rzecznik\w*)\b', re.IGNORECASE)

    for index, row in df.iterrows():
        print(f"[{index + 1}/{len(df)}] Analiza: {row['TICKET_ID']}...")

        llm_data = extract_data_with_llm(row['CUSTOMER_MESSAGE'])

        status = 'STANDARD_RETURN_PROCEDURE'
        if legal_pattern.search(str(row['CUSTOMER_MESSAGE'])):
            status = 'ESCALATE_LEGAL'
        elif (row['CATEGORY'] == "Bielizna") or ("Premium " in row['CATEGORY']):
            status = 'MANUAL_INSPECTION'
        elif (row['TOTAL_SPENT'] > 2500) and llm_data['zadanie'] != "Wymiana":
            status = 'AUTO_REFUND'
        elif llm_data['ocena'] <= 2 and llm_data['powod_zwrotu'] == "Opóźnienie w Dostawie":
            status = 'DISCOUNT_15'

        res_data = {
            'TICKET_ID': row['TICKET_ID'],
            'DATA_ZGŁOSZENIA': row['CREATED_AT'],
            'POWOD_ZWROTU': llm_data['powod_zwrotu'],
            'OCENA_KLIENTA': llm_data['ocena'],
            'STATUS': status,
            'WYGENEROWANA_ODPOWIEDZ': ""
        }

        if status in ['AUTO_REFUND', 'DISCOUNT_15', 'STANDARD_RETURN_PROCEDURE']:
            res_data['WYGENEROWANA_ODPOWIEDZ'] = generate_response_email(status, llm_data['powod_zwrotu'],
                                                                         llm_data['ocena'])
            raport_automatyczny.append(res_data)
        else:
            do_recznej_weryfikacji.append(res_data)

    pd.DataFrame(raport_automatyczny).to_csv("raport_automatyczny.csv", index=False)
    pd.DataFrame(do_recznej_weryfikacji).to_csv("do_weryfikacji_recznej.csv", index=False)
    print("✨ Przetwarzanie zakończone!")


if __name__ == "__main__":
    main()