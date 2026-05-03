# Review App

Sovelluksen toiminnot

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan arvosteluja.
- Käyttäjä pystyy luoda Arvosteluja eri kategorioihin (movie, game, series, song)
- Käyttäjä näkee sovellukseen lisätyt arvostelut.
- Käyttäjä pystyy etsimään ilmoituksia hakusanalla.
- Like/Dislike ja Favorite nappi jokaisessa arvosteluissa.
- Käyttäjä näkee sekä itse lisäämänsä että muiden käyttäjien lisäämät arvostelut ja kommentit.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja, käyttäjän lisäämät ilmoitukset ja käyttäjän suosikki arvostelut.

## Sovelluksen asennus

1. Kloonaa repositorio:

```
   git clone https://github.com/christian-escabillas/reviews.git
   cd reviews
```

2. Luo virtuaaliympäristö:

```
   python3 -m venv venv
   source venv/bin/activate
```

3. Asenna Flask:

```
   pip install flask
```

4. Luo tietokanta:

```
   sqlite3 database.db < schema.sql
```

5. Käynnistä sovellus:

```
   flask run
```

6. Avaa selaimessa:

```
   http://127.0.0.1:5000
```

## Projektin rakenne

- app.py – Flask-sovellus
- queries.py – tietokantakyselyt
- templates/ – HTML-sivut
- static/ – CSS ja kuvat
- schema.sql – tietokannan rakenne


