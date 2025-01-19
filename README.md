# kommune

Et Python script som henter alt fra Vågans kommune postliste: https://vagan.kommune.no/politikk-og-organisasjon/innsyn/postliste/

Siden søkefunksjonen for postlisten krever at man først velger _datoen_ man vil søke i, fungerer den dårlig.

## Hva skjer?

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

Greit å vite:
* Mellom hver dag tar scriuoptet en pause på 0-5 sekunder.
* Hvis en saksmappe (directory) allerede eksisterer, hopper scriptet over den saken.

## Hva lagres?

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

Greit å vite:
* For saker som er unntatt offentlighet lagres bare en `details.txt`.

## Hva får man se?

Scriptet er relativt pratsomt:

```
2024-08-05
  2021102111: 23/3527 - Barnevernsmappe
  2021102085: 22/762 - Basistilskuddsrapport for fastlegeordningen
    - Basistilskuddsrapport for fastlegeordningen i 1865 Vågan kommune per august 2024
    - 1865 - Vågan - august 2024
  2021102057: 24/1938 - GBN 5/30 - Egenerklæring konsesjonsfrihet
  2021102098: 23/610 - Gatelys Vågan
    - Gatelys på eiendom Straumnesveien 30 Laukvik
  2021102105: 24/1704 - Fastlege 100 % stilling - Legetorget legesenter Vågan kommune - st. ref. 4832957397Fastlege 100 % stilling - Legetorget legesenter
  2021102058: 24/1209 - Konkurranse - Utførelsesentreprise- Skrei E31 rørtekniske arbeider
  2021102056: 24/1937 - Tvangssalg
  2021102108: 24/1873 - Gbn 18/225, 18/2 og 18/155 - Støttemur Meieritomta - Storgata 50, SvolværVågan Kommune Drift Og Forvaltning Teknisk Drift
    - Meieritomta - Søknad om tillatelse i ett trinn 18_225 m.fl.
    - 2_KART_Situasjonsplan_Situasjonsplan Meieritomta.pdf
    - 3_TEGN_TegningNyFasade_J04.pdf
    - 4_TEGN_TegningNyttSnitt_recon_bs2012_a4.pdf
    - 5_TEGN_TegningNyttSnitt_J06.pdf
    - 6_TEGN_TegningEksisterendeSnitt_J05.pdf
    - 7_TEGN_TegningEksisterendeFasade_recon_bs2012_a4.pdf
    - 8_KORR_KvitteringNabovarsel_KvitteringNabovarsel.pdf
    - 9_ANKO_ErklaeringAnsvarsrett_ErklæringOmAnsvarsrett_Utførelse_Annet_928086429_OTTAR BERGERSEN _ SØNNER AS.pdf
    - 10_ANKO_ErklaeringAnsvarsrett_ErklæringOmAnsvarsrett_Prosjektering_PVUTEAR_979364857_COWI AS.pdf
    - 16_Gjennomføringsplan_Gjennomføringsplan.pdf
    - 17_KORR_Vedleggsopplysninger.pdf
    - 18_KORR_Opplysninger gitt i nabovarsel.pdf
  2021102110: 24/1012 - Startlån
  2021102109: 24/1812 - Gbn 14/56 - Ny enebolig med sokkelleilighet - Kretaveien 26Frida Grønhaug Ottemo
    - Supplering av søknad 14_56
    - 2_KORR_Annet_0_Supplerende dokumentasjon - Mangelskriv saknr. 24_17109.pdf
    - 3_TEGN_TegningNyFasade_1_1022-24 Fasader Skisse Rev. D. 20.06.24.pdf
    - 4_KORR_SamtykkePlassering_2_Q1 - Avstandserklæring gbnr. 14_56 og 14_85.pdf
    - 5_TEGN_TegningEksisterendePlan_3_Plantegning_ snitt og situasjonsplan.pdf
    - 7_KORR_Vedleggsopplysninger.pdf
2024-08-06
```






