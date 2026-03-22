# SANDMARK

Prosta aplikacja do pobierania diffa z GitLab MR i uruchamiania review przez Gemini.

## Wymagania

- Python 3.11+ (zalecane)
- Klucz API Gemini (`GEMINI_API_KEY`)
- (Opcjonalnie) token GitLab (`GITLAB_TOKEN`) dla prywatnych repozytoriów

## 1) Instalacja lokalna

W katalogu projektu uruchom:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Konfiguracja `.env`

W głównym katalogu projektu utwórz plik `.env`:

```env
GEMINI_API_KEY=twoj_klucz_gemini
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=
```

Uwagi:
- `GITLAB_TOKEN` może być pusty dla publicznych MR.
- Dla self-hosted GitLaba ustaw własny `GITLAB_URL` (np. `https://gitlab.twojafirma.local`).

## 3) Uruchomienie backendu

W aktywnym virtualenv:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API będzie dostępne pod adresem:
- `http://localhost:8000`
- dokumentacja Swagger: `http://localhost:8000/docs`

## 4) Uruchomienie frontendu

Najprościej uruchomić statyczny serwer dla folderu `frontend`:

```powershell
python -m http.server 5500 --directory frontend
```

Następnie otwórz:
- `http://localhost:5500`

Frontend jest skonfigurowany na backend: `http://localhost:8000`.

## 5) Szybki test

1. Otwórz UI (`http://localhost:5500`).
2. Wklej URL do GitLab MR w formacie:
   `https://gitlab.com/<project_path>/-/merge_requests/<id>`
3. Kliknij `Fetch Diff`, wybierz prompt, potem `Run Review`.

## Typowe problemy

- `GEMINI_API_KEY is not set`  
  Sprawdź czy `.env` jest w katalogu głównym i czy backend został zrestartowany.

- `Invalid GitLab MR URL`  
  Użyj pełnego URL MR z `/-/merge_requests/<id>`.

- Błąd 401/403 z GitLaba  
  Ustaw poprawny `GITLAB_TOKEN` (zwłaszcza dla prywatnych projektów).