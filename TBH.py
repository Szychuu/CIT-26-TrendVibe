import pandas as pd
import json
import os
import re
import time
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja klienta Gemini
# Upewnij się, że masz ustawioną zmienną środowiskową GEMINI_API_KEY w swoim pliku .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_data_with_llm(message, retries=3):
    """
    Wysyła wiadomość klienta do modelu LLM w celu ekstrakcji danych.
    Dzięki Gemini natywnie wymuszamy idealny format JSON.
    """
    prompt = f"""
    Przeanalizuj poniższą wiadomość od klienta i zwróć DOKŁADNIE i TYLKO obiekt JSON.
    Format JSON:
    {{
        "powod_zwrotu": "Uszkodzenie" | "Zły Rozmiar" | "Opóźnienie w Dostawie" | "Inne",
        "ocena": liczba całkowita od 1 do 5 (jeśli brak, wpisz 3),
        "zadanie": "Zwrot Środków" | "Wymiana" | "Brak Sprecyzowania"
    }}
    Wiadomość klienta: "{message}"
    """
    
    # Inicjalizacja modelu Gemini Pro
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    for attempt in range(retries):
        try:
            # Wymuszamy format JSON - wbudowana funkcja Gemini
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            
            content = response.text.strip()
            return json.loads(content)
            
        except json.JSONDecodeError:
            print(f"  [!] Próba {attempt+1}: Model nie zwrócił poprawnego JSONa. Próbuję ponownie...")
            time.sleep(1)
        except Exception as e:
            print(f"  [!] Próba {attempt+1}: Błąd API: {e}. Próbuję ponownie...")
            time.sleep(2)
            
    # Wartości domyślne w przypadku całkowitego niepowodzenia
    return {"powod_zwrotu": "Inne", "ocena": 3, "zadanie": "Brak Sprecyzowania"}

def generate_response_email(status, reason, rating, retries=2):
    """
    Generuje spersonalizowaną odpowiedź mailową dla klienta.
    """
    prompt = f"""
    Jesteś asystentem obsługi klienta w sklepie TrendVibe.
    Napisz krótką, profesjonalną i uprzejmą odpowiedź do klienta.
    
    Wytyczne do treści na podstawie decyzji:
    - Decyzja: {status}
    - Powód zwrotu podany przez klienta: {reason}
    - Ocena klienta: {rating}/5
    
    Jeśli status to AUTO_REFUND: Poinformuj o zwrocie pieniędzy, który nastąpi w ciągu 3 dni.
    Jeśli status to DISCOUNT_15: Przeproś za niedogodności, zaoferuj kod rabatowy TREND15 na kolejne zakupy.
    Jeśli status to STANDARD_RETURN_PROCEDURE: Poinformuj, że zgłoszenie zostało przyjęte i oczekuje na standardowe rozpatrzenie w centrum logistycznym.
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    for attempt in range(retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7
                )
            )
            return response.text.strip()
        except Exception as e:
            time.sleep(2)
            
    return "Dzień dobry. Twoje zgłoszenie zostało przyjęte do realizacji. Skontaktujemy się z Tobą wkrótce. Pozdrawiamy, Zespół TrendVibe."

def main():
    print("Rozpoczynam pracę systemu Sprytne Zwroty AI...")

    # 1. Wczytanie danych z plików CSV
    try:
        zgloszenia = pd.read_csv("zgloszenia_BOK.csv")
        klienci = pd.read_csv("klienci_historia.csv")
        # Zabezpieczenie przed polskimi znakami w nazwie pliku
        plik_produkty = "katalog_produktow.csv" if os.path.exists("katalog_produktow.csv") else "katalog_produktów.csv"
        produkty = pd.read_csv(plik_produkty)
    except FileNotFoundError as e:
        print(f"Błąd: Nie znaleziono pliku. Upewnij się, że wypakowałes pliki CSV do tego samego folderu co skrypt. Szczegóły: {e}")
        return

    # Przygotowanie dat
    zgloszenia['CREATED_AT'] = pd.to_datetime(zgloszenia['CREATED_AT'])
    dzisiejsza_data = zgloszenia['CREATED_AT'].max()

    # Łączenie danych
    df = zgloszenia.merge(klienci, on="CUSTOMER_ID", how="left")
    df = df.merge(produkty, on="PRODUCT_ID", how="left")

    raport_automatyczny = []
    do_recznej_weryfikacji = []

    # Wyrażenie regularne szukające słów związanych z prawem (\b oznacza granicę słowa)
    legal_pattern = re.compile(r'\b(prawnik\w*|uokik|sąd\w*|rzecznik\w*)\b', re.IGNORECASE)

    # 2. Przetwarzanie zgłoszeń
    print(f"Do przetworzenia: {len(df)} zgłoszeń.")
    
    for index, row in df.iterrows():
        print(f"Przetwarzanie zgłoszenia: {row['TICKET_ID']} ({index + 1}/{len(df)})...")
        
        # Ekstrakcja z LLM
        llm_data = extract_data_with_llm(row['CUSTOMER_MESSAGE'])
        powod = llm_data.get('powod_zwrotu', 'Inne')
        ocena = llm_data.get('ocena', 3)
        zadanie = llm_data.get('zadanie', 'Brak Sprecyzowania')
        
        # Logika Biznesowa
        status = None
        message_str = str(row['CUSTOMER_MESSAGE'])
        kategoria = str(row['CATEGORY'])
        
        is_vip = (row['TOTAL_SPENT'] > 2500) and (row['RETURN_RATE'] < 0.3)
        
        # Reguła 1: Prawna
        if legal_pattern.search(message_str):
            status = 'ESCALATE_LEGAL'
            
        # Reguła 2: Premium
        elif "Premium" in kategoria or kategoria == "Bielizna":
            status = 'MANUAL_INSPECTION'
            
        # Reguła 3: VIP
        elif is_vip and kategoria != "Bielizna" and zadanie != "Wymiana":
            status = 'AUTO_REFUND'
            
        # Reguła 4: Regular
        elif (ocena == 1 or ocena == 2) and powod == "Opóźnienie w Dostawie" and not is_vip:
            status = 'DISCOUNT_15'
            
        # Reguła 5: Domyślnie
        else:
            status = 'STANDARD_RETURN_PROCEDURE'

        # Generowanie akcji i przydział do odpowiedniego pliku
        if status in ['AUTO_REFUND', 'DISCOUNT_15', 'STANDARD_RETURN_PROCEDURE']:
            odpowiedz = generate_response_email(status, powod, ocena)
            raport_automatyczny.append({
                'TICKET_ID': row['TICKET_ID'],
                'CUSTOMER_ID': row['CUSTOMER_ID'],
                'ORDER_ID': row['ORDER_ID'],
                'PRODUCT_ID': row['PRODUCT_ID'],
                'CUSTOMER_MESSAGE': row['CUSTOMER_MESSAGE'],
                'POWOD_ZWROTU': powod,
                'OCENA': ocena,
                'STATUS': status,
                'WYGENEROWANA_ODPOWIEDZ': odpowiedz,
                'DATA_ROZPATRZENIA': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            do_recznej_weryfikacji.append({
                'TICKET_ID': row['TICKET_ID'],
                'CUSTOMER_ID': row['CUSTOMER_ID'],
                'ORDER_ID': row['ORDER_ID'],
                'PRODUCT_ID': row['PRODUCT_ID'],
                'CUSTOMER_MESSAGE': row['CUSTOMER_MESSAGE'],
                'CREATED_AT': row['CREATED_AT'], 
                'POWOD_ZWROTU': powod,
                'OCENA': ocena,
                'STATUS': status,
                'DATA_ROZPATRZENIA': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    # 3. Sortowanie i Zapis
    if raport_automatyczny:
        df_auto = pd.DataFrame(raport_automatyczny)
        df_auto['DATA_ROZPATRZENIA'] = pd.to_datetime(df_auto['DATA_ROZPATRZENIA'])
        df_auto = df_auto.sort_values(by='DATA_ROZPATRZENIA')
        df_auto.to_csv("raport_automatyczny.csv", index=False, encoding='utf-8')
        print("Zapisano raport_automatyczny.csv")

    if do_recznej_weryfikacji:
        df_manual = pd.DataFrame(do_recznej_weryfikacji)
        
        # Kolejka priorytetowa dla zgłoszeń ręcznych
        df_manual['DNI_OCZEKIWANIA'] = (dzisiejsza_data - df_manual['CREATED_AT']).dt.days
        df_manual['ZAGROZONE_30_DNI'] = df_manual['DNI_OCZEKIWANIA'] >= 25
        df_manual['CZY_LEGAL'] = df_manual['STATUS'] == 'ESCALATE_LEGAL'
        
        # Sortujemy
        df_manual = df_manual.sort_values(
            by=['ZAGROZONE_30_DNI', 'CZY_LEGAL', 'CREATED_AT'], 
            ascending=[False, False, True]
        )
        
        # Usuwamy kolumny pomocnicze użyte do sortowania
        df_manual = df_manual.drop(columns=['DNI_OCZEKIWANIA', 'ZAGROZONE_30_DNI', 'CZY_LEGAL'])
        
        df_manual.to_csv("do_weryfikacji_recznej.csv", index=False, encoding='utf-8')
        print("Zapisano do_weryfikacji_recznej.csv")

    print("Zakończono pracę z sukcesem!")

if __name__ == "__main__":
    main()
