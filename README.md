# 📦 “Sprytne Zwroty AI” dla TrendVibe
> Prototyp systemu automatyzacji zwrotów i reklamacji dla dynamicznie rozwijającego się sklepu internetowego.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Consult IT](https://img.shields.io/badge/Competition-Consult%20IT%202026-orange)

## 🎯 Cel projektu
Projekt rozwiązuje problem niewydolności operacyjnej sklepu **TrendVibe**. Naszym celem było stworzenie narzędzia, które:
1. **Redukuje koszty** dzięki automatycznej weryfikacji zgłoszeń na pierwszym etapie e-obsługi.
2. **Optymalizuje logistykę** zwrotów, przyjmuje i kategoryzuje wiadomości od klientów, a następnie generuje gotową odpowiedź.
3. **Minimalizuje frustrację klienta** poprzez natychmiastową reakcję systemu.

## 🚀 Instalacja i Uruchomienie
```bash
# Klonowanie repozytorium
git clone https://github.com/Szychuu/CIT-26-TrendVibe.git
cd CIT-26-TrendVibe

# Instalacja bibliotek
pip install -r requirements.txt

# Konfiguracja (Kopiowanie wzoru i uzupełneinie kluczy)
cp .env.example .env
```

## ⚙️ Jak to działa? (Logika biznesowa)
System przyjmuje zgłoszenie reklamacyjne, a następnie:
* **Analizuje treść** za pomocą API.
* **Kategoryzuje** problem (zwrot/uszkodzenie/opóźnienie).
* **Generuje decyzję** automatyczna wiadomość zwrotna lub przekazanie do ręcznej weryfikacji.

## 🛠 Technologie
* **Python 3.12** – Serce systemu.
* **Gemini 3 Flash Preview** – Odpowiada za sortowanie reklamacji, priorytetyzację zgłoszeń oraz automatyzację komunikacji z klientem.

## 👥 Skład zespołu
* **Tomasz Rowiński** – Backend & Logic
* **Borys Szycher** – API Integration
