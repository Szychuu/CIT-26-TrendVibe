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
* **Analizuje treść** (np. za pomocą API do analizy tekstu).
* **Kategoryzuje** problem (zwrot/uszkodzenie/pomyłka).
* **Generuje decyzję** (np. automatyczna etykieta zwrotna lub przekazanie do konsultanta).

## 🛠 Technologie
* **Python 3.12** – Serce systemu.
* **[Nazwa API]** – Wykorzystane do [np. analizy sentymentu/generowania odpowiedzi].

## 👥 Skład zespołu
* **Tomasz Rowiński** – Backend & Logic
* **Borys Szycher** – API Integration & Data Flow
