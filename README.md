# Reviews

Sovelluksen perusvaatimukset ovat:

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen. (Done)
- Käyttäjä pystyy lisäämään sovellukseen arvosteluja. Lisäksi käyttäjä pystyy muokkaamaan ja poistamaan lisäämiään arvoteluja. (Done)
- Käyttäjä näkee sovellukseen lisätyt arvostelut. (Done)
- Käyttäjä näkee sekä itse lisäämänsä että muiden käyttäjien lisäämät arvostelut ja kommentit. (Done)
- Käyttäjä pystyy etsimään tietokohteita hakusanalla tai muulla perusteella. (Done)
- Käyttäjä pystyy hakemaan sekä itse lisäämiään että muiden käyttäjien lisäämiä arvosteluja. (Done)
- Sovelluksessa on käyttäjäsivut, jotka näyttävät jokaisesta käyttäjästä tilastoja ja käyttäjän lisäämät arvostelut. (Half done)
- Käyttäjä pystyy valitsemaan tietokohteelle yhden tai useamman luokittelun. Mahdolliset luokat ovat tietokannassa. (Done)
- Sovelluksessa on pääasiallisen tietokohteen lisäksi toissijainen tietokohde, joka täydentää pääasiallista tietokohdetta.
- Käyttäjä pystyy lisäämään toissijaisia tietokohteita omiin ja muiden käyttäjien tietokohteisiin liittyen.

## Sovelluksen asennus

```
pip install flask
```

Luo tietokanna taulut ja lisää alkutiedot:

```
sqlite3 database.db < schema.sql
```

Käynnistys:

```
flask run
```

Avaa selaimessa:
http://127.0.0.1:5000/

## Rakenne
- 'app.py' - pääsovellus
- 'templates/' HTML-tiedostot
- schema.sql - tietokannan rakenne



