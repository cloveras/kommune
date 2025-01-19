# kommune

Henter alt fra Vågans kommune postliste: https://vagan.kommune.no/politikk-og-organisasjon/innsyn/postliste/

Siden søkefunksjonen for postlisten krever at man først velger _datoen_ man vil søke i, fungerer den dårlig.

Dette scriptet henter ned alle saker mellom to datoer, og lager en mappestruktur `archive/YYYY/MM/DD/<sak>`, som dette:

```
$ ls -1 archive/2024/01/17/
2021085354 - 22_2334 - Samhandlingsavvik/
2021085356 - 24_7 - Skjenkebevilling - Enkeltanledning_Ambulerende 2024/
2021085362 - 24_12 - Henvendelser Drift og forvaltning 2024/
2021085387 - 24_134 - Eierskapsenheten - Leie av kommunal bolig/
2021085388 - 23_1389 - GBN 5_1_108 - OppmålingO-13_2020/
2021085389 - 24_134 - Eierskapsenheten - Leie av kommunal bolig/
2021085394 - 24_134 - Eierskapsenheten - Leie av kommunal bolig/
2021085408 - 21_2298 - Detaljregulering - Samlagstomta - Planid 314 - Kabelvåg_ Gbn 13_325/
2021085414 - 21_2298 - Detaljregulering - Samlagstomta - Planid 314 - Kabelvåg_ Gbn 13_325/
2021085422 - 18_303 - Høringer - stab_støtte/
```

For hver sak lages det en fil `details.txt`, og alle sakens dokumenter lasted ned til samme mappe. Et eksempel:

```
$ cat "archive/2024/01/17/2021085388 - 23_1389 - GBN 5_1_108 - OppmålingO-13_2020/details.txt"
DokumentID: 24/1185 - Angående oppmåling - Gbn 5/1/108Utkjøp av festetomt Henningsvær - Gbn 5/1/108
ArkivsakID: 23/1389 - GBN 5/1/108 - OppmålingO-13/2020
Journaldato: 17.01.2024
Brevdato: 17.01.2024
Dokumentansvarlig: Ida Hegreberg
Journalpostkategori: Epost

Avsender(e):
Erling Benjamen Andersen
Ullevålsveien 47 A
0171 OSLO

Angående oppmåling - Gbn 5/1/108
```





