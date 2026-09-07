<div align="center">

# 📺 IPTV Checker

**Playlist inspection & channel management tool by Swir**  
**Narzędzie do sprawdzania playlist i zarządzania kanałami IPTV**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52)
![Async](https://img.shields.io/badge/Networking-aiohttp-2C5BB4)

</div>

---

## 🇵🇱 Polski

IPTV Checker to desktopowa aplikacja PyQt5 do pracy z playlistami IPTV/M3U. Pozwala wczytać adresy, przeglądać i filtrować kanały, zapisać playlistę oraz uruchomić wybrany strumień w VLC.

### ✨ Funkcje
- wprowadzanie wielu adresów IPTV
- asynchroniczna obsługa połączeń z `aiohttp`
- filtrowanie kanałów po fragmencie nazwy
- grupowanie i przeglądanie znalezionych kanałów
- pobieranie playlist
- uruchamianie wybranych pozycji w VLC
- ręczny wybór ścieżki VLC
- polska i angielska wersja skryptu

### 🚀 Instalacja
```bash
git clone https://github.com/Swir/IPTV-checker.git
cd IPTV-checker
pip install aiohttp PyQt5
python checker.py
```

Wersja angielska:
```bash
python "checker english.py"
```

> Używaj aplikacji wyłącznie z playlistami i strumieniami, do których masz prawo dostępu.

---

## 🇬🇧 English

IPTV Checker is a PyQt5 desktop application for working with IPTV/M3U playlists. It can load addresses, browse and filter channels, save playlists and launch selected streams in VLC.

### ✨ Features
- multiple IPTV URL input
- asynchronous networking with `aiohttp`
- channel-name filtering
- channel browsing and grouping
- playlist downloading
- VLC playback integration
- manual VLC executable selection
- Polish and English script variants

### 🚀 Installation
```bash
git clone https://github.com/Swir/IPTV-checker.git
cd IPTV-checker
pip install aiohttp PyQt5
python "checker english.py"
```

> Use the application only with playlists and streams you are authorized to access.

---

## 👤 Author / Autor
Developed by **Swir**.
