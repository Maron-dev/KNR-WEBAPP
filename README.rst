Webcam server
=============
1. Instalacja pakietów
$ pip install aiohttp aiortc
ur browser:

2. Uruchomienie kilenta Tailscale
$ sudo tailscale up

3. Uruchomienie aplikacji Webowej
$ python3 webcam.py

4. Sprawdzenie działania aplikacji lokalnie
Otwórz przeglądarkę i wpisz adres http://localhost:8080
Następnie zaznacz opcje "use STUN server" i kliknij "Start"
(Czas zanim kamera zacznie działać może być różny, w zależności od urządzenia i przeglądarki)
Nie dłużej niż minuta

5. W innym terminalu uruchom tailscale funnel
$ sudo tailscale funnel 8080

5. Po wykonaniu poprzedniego kroku otrzymasz publiczny adres URL, który możesz udostępnić innym osobom, aby mogły zobaczyć strumień wideo z Twojej kamery. Adres ten będzie wyglądał mniej więcej tak: https://<random-string>.ts.net
Np. https://twoj-serwer.ts.net

6. Otwórz stronę na innym urządzeniu, podłączonym do innej sieci
https://twoj-serwer.ts.net

7. Po kliknięciu "Start" na stronie, strumień wideo z Twojej kamery powinien być widoczny na drugim urządzeniu.
Tym razem nie zaznaczaj opcji "use STUN server"
