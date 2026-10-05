# Momentum gestito per il rischio: replica e test dopo il 2011

In questo progetto replico la strategia di Barroso e Santa-Clara (2015), "Momentum has its moments". La base è il momentum lungo-corto di Jegadeesh e Titman (1993): comprare i titoli che sono saliti di più nell'ultimo anno e vendere allo scoperto quelli scesi di più. Nella versione del paper l'esposizione è scalata in base alla volatilità prevista. Poi provo la strategia sul periodo successivo ai dati del paper, gennaio 2012 - agosto 2026, con le stesse regole e senza scegliere io i parametri della strategia.

Le domande sono due: **la gestione del rischio riduce i crolli del momentum anche dopo il 2011?** E **migliora il rendimento per unità di rischio (Sharpe)?**

## Indice

1. [Risultato in breve](#1-risultato-in-breve)
2. [Come ho lavorato](#2-come-ho-lavorato)
3. [Dati](#3-dati)
4. [Il metodo in quattro passi](#4-il-metodo-in-quattro-passi)
5. [Cosa confronto](#5-cosa-confronto)
6. [Risultati](#6-risultati)
7. [Limiti](#7-limiti)
8. [Come riprodurre i numeri](#8-come-riprodurre-i-numeri)
9. [Struttura del repository](#9-struttura-del-repository)
10. [Riferimenti](#10-riferimenti)

I dettagli tecnici (formule, convenzioni, bootstrap, costi, controlli sui dati) sono in [docs/metodo.md](docs/metodo.md). In [docs/domande_e_risposte.md](docs/domande_e_risposte.md) ci sono le risposte brevi alle domande più probabili.

---

## 1. Risultato in breve

Sul periodo di test (gennaio 2012 - agosto 2026, 176 mesi), rendimenti lordi:

- **Il rischio scende molto.** Il drawdown massimo passa dal 64,8% al 23,0%, il mese peggiore da −32,1% a −12,5%, la curtosi in eccesso da 2,10 a 1,05. L'ipotesi sul rischio, fissata prima del test, è confermata: dovevano migliorare tutte e tre le misure. Buona parte di questo calo viene però dalla sola esposizione più bassa. Confrontato con il semplice ridotto alla stessa volatilità (confronto fatto dopo il test), il gestito ha ancora un drawdown più basso (−23,0% contro −32,7%) e metà curtosi, ma quasi lo stesso mese peggiore (−12,5% contro −13,6%).
- **Lo Sharpe sale da 0,197 a 0,375.** La differenza, calcolata sui valori non arrotondati, è +0,177, con intervallo al 95% [+0,003; +0,333]. Secondo la regola fissata prima è "evidenza di miglioramento", ma il limite inferiore è appena sopra lo zero: è un'evidenza al limite. Con blocchi del bootstrap più corti (1 o 3 mesi) l'intervallo include lo zero, e un test classico (Jobson-Korkie con la correzione di Memmel) dà p = 0,069.
- **Il momentum in sé è andato male dopo il 2011.** Sharpe 0,20 per il semplice e 0,37 per il gestito, nessuno dei due distinguibile da zero. Il mercato azionario nello stesso periodo ha Sharpe 0,94.
- **Con i costi il quadro peggiora.** Con lo scenario medio (prestito titoli 0,5%, negoziazione 2% annuo) lo Sharpe del gestito scende a 0,19 e la differenza con il semplice non è più distinguibile da zero. Con lo scenario alto il lungo-corto non rende.

In sintesi: la gestione della volatilità fa quello che promette, cioè taglia i crolli, e questo regge fuori campione. Il vantaggio sullo Sharpe c'è, ma è piccolo, si concentra nel 2016-2026 e dipende dall'ipotesi di costi zero.

![Crescita del capitale nel test](img/capitale_test.png)

## 2. Come ho lavorato

Il rischio maggiore in un progetto come questo è ingannarsi da soli, provando varianti finché una funziona. Per evitarlo ho fissato tutto prima di guardare il periodo di test.

- **Regole dal paper.** Volatilità obiettivo 12%, 126 giorni per la stima, ribilanciamento mensile, nessun tetto alla leva: sono le scelte di Barroso e Santa-Clara. Le scelte mie riguardano solo la valutazione (bootstrap, sottoperiodi, scenari di costo) e le ho fissate prima del test.
- **Replica come verifica del codice.** Prima ho rifatto i conti sul periodo del paper (1927-2011). La condizione per proseguire era ritrovare gli Sharpe del paper entro ±0,10. Se la replica non fosse tornata, avrei cercato l'errore prima di andare avanti.
- **Criteri scritti prima del test.** In [docs/criteri_del_verdetto.md](docs/criteri_del_verdetto.md) ci sono le due ipotesi e la regola di decisione. Il repository non può provare quando li ho scritti, quindi è una mia dichiarazione. La configurazione è congelata in `config_congelata.json` insieme all'impronta SHA-256 dei criteri.
- **Test eseguito una volta.** `scripts/04_test_fuori_campione.py` si rifiuta di partire se i criteri sono cambiati, se la configurazione non coincide con i valori del codice o se nella copia di lavoro l'esito esiste già. È una protezione contro i rilanci per errore, non una garanzia: chi clona il repository può rieseguirlo, e deve ottenere lo stesso testo. L'esito originale è in [docs/esito_test.txt](docs/esito_test.txt).
- **Analisi dopo il test, dichiarate come tali.** La sensibilità del bootstrap, il confronto a pari volatilità, il meccanismo e i mesi di crollo li ho calcolati dopo ([docs/analisi_dopo_il_test.txt](docs/analisi_dopo_il_test.txt)). Aiutano a leggere il risultato, ma non cambiano il verdetto.

Le due ipotesi:

1. **Rischio:** il WML gestito ha drawdown massimo, mese peggiore e curtosi in eccesso più bassi del WML semplice. È confermata solo se migliorano tutte e tre.
2. **Sharpe (misura primaria):** differenza di Sharpe gestito meno semplice, con intervallo al 95% da bootstrap stazionario. Evidenza se l'intervallo è tutto sopra lo zero; indicazione debole se la stima è positiva ma l'intervallo include lo zero; altrimenti nessun miglioramento.

## 3. Dati

Tutti i dati vengono dalla [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) (versione costruita sul database CRSP 202608). Sono gratuiti e non soffrono di distorsione da sopravvivenza, perché i portafogli includono anche i titoli poi usciti dal listino.

| File | Uso |
|---|---|
| 10 portafogli sul momentum, mensili | WML = decile vincente meno decile perdente; decile vincente solo lungo |
| 10 portafogli sul momentum, giornalieri | WML giornaliero, solo per stimare la volatilità |
| Fattore Mom, mensile e giornaliero | robustezza: la versione di French del momentum (6 portafogli taglia × momentum) |
| 6 portafogli taglia × momentum | controllo: il fattore Mom si ricostruisce da questi |
| 3 fattori, mensili e giornalieri | mercato (Mkt-RF) e tasso privo di rischio (RF) |

Periodi: mensili da gennaio 1927 ad agosto 2026 (1.196 mesi), giornalieri dal 3 novembre 1926 al 31 agosto 2026 (26.216 giorni). `scripts/01_controlla_dati.py` verifica che non ci siano valori mancanti né mesi saltati, che i quattro file giornalieri abbiano gli stessi giorni, che il fattore Mom si ricostruisca dai 6 portafogli (differenza massima 0,01 punti, cioè l'arrotondamento) e che il mercato mensile coincida con il composto dei giornalieri.

Un dettaglio importante: i portafogli mensili sono ricostituiti ogni mese (rendimento passato da t−12 a t−2), quelli giornalieri ogni giorno. I rendimenti della strategia vengono sempre dai file mensili; i giornalieri servono solo a stimare la volatilità.

I dati non sono nel repository: `scripts/00_scarica_dati.py` li scarica (controllando prima il robots.txt), oppure si scaricano a mano (istruzioni nello script).

## 4. Il metodo in quattro passi

1. **Momentum (WML).** Ogni mese il rendimento di WML è il decile dei vincenti meno quello dei perdenti, pesati per capitalizzazione. La strategia è autofinanziata (lo scoperto finanzia l'acquisto), quindi il suo rendimento è già un rendimento in eccesso.
2. **Volatilità prevista.** Alla fine del mese t−1 prendo gli ultimi 126 rendimenti giornalieri di WML (circa sei mesi; prima del 1952 si contrattava anche il sabato, quindi circa cinque) e calcolo la varianza mensile come 21 × media dei quadrati. La volatilità annua è la radice di 12 volte la varianza mensile.
3. **Peso.** Peso del mese t = 12% / volatilità prevista. Se il momentum è agitato il peso scende sotto 1, se è calmo sale sopra 1. Non c'è un tetto.
4. **Rendimento gestito.** Rendimento del mese t = peso × WML del mese t. Il peso usa solo dati fino al mese prima: lo controllano i test (alterare i giorni del mese t non cambia il peso del mese t; troncare i dati non cambia i pesi passati).

L'idea economica: la volatilità del momentum è molto persistente e si prevede bene, mentre il suo rendimento medio non è più alto quando la volatilità è alta. Scalando per la volatilità si toglie soprattutto rischio, non rendimento atteso. Secondo Daniel e Moskowitz (2016) i crolli del momentum arrivano soprattutto quando, dopo un ribasso del mercato e in fasi di alta volatilità, il mercato rimbalza e i titoli perdenti (la gamba corta) salgono di colpo: sono periodi in cui la volatilità prevista era già alta.

![Peso nel tempo](img/peso_nel_tempo.png)

## 5. Cosa confronto

| Serie | Perché |
|---|---|
| WML semplice | il riferimento principale: stessa strategia senza gestione del rischio |
| Fattore Mom di French, semplice e gestito | robustezza: un'altra costruzione del momentum (sei portafogli, 30% estremi) |
| Decile vincente solo lungo, semplice e gestito | quanto conta la gamba corta |
| Mercato (Mkt-RF) | il confronto naturale per chi investe |
| Mercato + WML gestito | il momentum gestito aggiunto a un portafoglio di mercato |

Tutte le serie sono rendimenti mensili in eccesso sul tasso privo di rischio. Sharpe annuo = media / deviazione standard × √12.

## 6. Risultati

### 6.1 Replica del paper (maggio 1927 - dicembre 2011, 1.016 mesi)

| | Sharpe | paper | Curtosi in eccesso | paper | Mese peggiore | paper |
|---|---|---|---|---|---|---|
| WML semplice | 0,54 | 0,53 | 17,95 | 18,24 | −77,66% | −78,96% |
| WML gestito | 1,00 | 0,97 | 2,00 | 2,68 | −24,16% | −28,40% |

I pesi vanno da 0,14 a 2,09 (nel paper 0,13-2,00). La replica è superata ([docs/esito_replica.txt](docs/esito_replica.txt)). Sugli Sharpe la distanza è piccola; sulle code del gestito è più ampia (curtosi 2,00 contro 2,68, mese peggiore −24,2% contro −28,4%). Le cause probabili, che non ho verificato una per una, sono la versione più recente del database CRSP, il WML giornaliero ricostituito ogni giorno che uso per la volatilità e un mese iniziale forse diverso da quello del paper.

### 6.2 Test fuori campione (gennaio 2012 - agosto 2026, 176 mesi)

| | Media annua | Volatilità | Sharpe | Curtosi | Mese peggiore | Drawdown massimo |
|---|---|---|---|---|---|---|
| WML semplice | 5,70% | 28,89% | 0,20 | 2,10 | −32,08% | −64,77% |
| **WML gestito** | 4,58% | 12,22% | 0,37 | 1,05 | −12,52% | −23,03% |
| Mom di French | 2,40% | 13,28% | 0,18 | 2,26 | −16,21% | −25,38% |
| Mom gestito | 4,36% | 11,35% | 0,38 | 0,77 | −9,71% | −18,56% |
| Vincenti solo lunghi | 17,81% | 21,48% | 0,83 | 2,91 | −15,81% | −31,28% |
| Vincenti gestiti | 9,31% | 11,07% | 0,84 | 1,78 | −10,82% | −14,04% |
| Mercato | 13,57% | 14,48% | 0,94 | 0,97 | −13,37% | −25,28% |
| Mercato + WML gestito | 18,15% | 16,39% | 1,11 | 0,80 | −12,49% | −18,80% |

**Verdetto.** Ipotesi 1 (rischio): confermata. Ipotesi 2 (Sharpe): differenza +0,177, intervallo al 95% [+0,003; +0,333], quindi "evidenza di miglioramento" per la regola fissata prima, al limite.

Altre letture (descrittive):

- **Robustezza con il fattore Mom:** stessa direzione, differenza di Sharpe +0,203 [+0,023; +0,361].
- **Alfa:** regredendo il gestito sul semplice, alfa del 2,33% annuo (t = 2,31, errori di Newey e West) con beta 0,39. Il gestito non è solo una versione ridotta del semplice.
- **Peso:** nel test va da 0,18 a 0,99, con media 0,50. La volatilità prevista del momentum è stata sempre sopra il 12%, quindi la strategia non ha mai usato leva.
- **Pari volatilità (dopo il test):** il WML semplice moltiplicato per 0,423 ha la stessa volatilità del gestito (12,22%). Rispetto a questa versione il gestito ha drawdown −23,0% contro −32,7%, curtosi 1,05 contro 2,10 e mese peggiore −12,5% contro −13,6%. Il guadagno che viene dal "quando" ridurre l'esposizione, e non solo dal "quanto", è quindi reale ma più piccolo di quello che dice il confronto diretto.
- **Solo lungo:** gestire la volatilità dimezza volatilità e drawdown, ma non cambia lo Sharpe (0,83 contro 0,84; differenza +0,012 [−0,172; +0,176]): qui agisce solo come riduzione dell'esposizione. È coerente con l'idea che il guadagno sullo Sharpe passi dalla gamba corta.
- **Mercato + WML gestito:** Sharpe 1,11 contro 0,94 del mercato e drawdown −18,8% contro −25,3%. La differenza di Sharpe (+0,170 [−0,173; +0,468]) però non è distinguibile da zero.

![Drawdown nel test](img/drawdown_test.png)

### 6.3 Dove nasce il miglioramento

| Mese | WML semplice | Peso | WML gestito | Mercato | Vincenti | Perdenti |
|---|---|---|---|---|---|---|
| aprile 2020 | −32,08% | 0,39 | −12,52% | +13,60% | +14,67% | +46,75% |
| novembre 2020 | −27,10% | 0,20 | −5,44% | +12,45% | +10,38% | +37,48% |
| luglio 2026 | −22,71% | 0,26 | −5,93% | −0,61% | −15,41% | +7,30% |
| febbraio 2021 | −22,57% | 0,23 | −5,16% | +2,81% | −2,78% | +19,79% |
| gennaio 2023 | −21,58% | 0,26 | −5,59% | +6,61% | +0,52% | +22,10% |

I cinque mesi peggiori del semplice arrivano tutti con un peso tra 0,20 e 0,39, sotto la media del test (0,50), deciso con i dati del mese prima. In quattro casi su cinque il crollo viene dal rimbalzo dei perdenti, con il mercato in rialzo. È simile al meccanismo di Daniel e Moskowitz, anche se solo aprile 2020 e gennaio 2023 arrivano dopo due anni di mercato in calo, e di poco (−0,7% e −0,8%). Luglio 2026 è diverso: lì sono crollati i vincenti. La volatilità prevista ha una correlazione di +0,65 con quella realizzata nel mese dopo: il rischio si prevede bene. Con il rendimento del WML la correlazione è −0,14 (t ≈ −1,9): nel test il rendimento non sale quando la volatilità prevista è alta, ma questo da solo non è statisticamente distinguibile da zero.

Per sottoperiodi il quadro è meno uniforme. Nel 2012-2015 le due versioni hanno lo stesso Sharpe (0,59 contro 0,60). Nel 2016-2026 il semplice scende a 0,10 e il gestito tiene 0,29.

![Sharpe per periodo](img/sharpe_per_periodo.png)

### 6.4 Costi

I file di French non dicono quanto si scambia, quindi i costi sono ipotesi esplicite (dettagli in [docs/metodo.md](docs/metodo.md)):

| Scenario | Prestito titoli | Negoziazione | Variazione del peso | Sharpe semplice | Sharpe gestito | Differenza [IC 95%] |
|---|---|---|---|---|---|---|
| lordo | 0% | 0% | 0 pb | 0,20 | 0,37 | +0,177 [+0,003; +0,333] |
| medio | 0,5% | 2% | 10 pb | 0,04 | 0,19 | +0,144 [−0,029; +0,298] |
| alto | 1% | 4% | 20 pb | −0,11 | 0,00 | +0,110 [−0,062; +0,263] |

Il gestito resta davanti al semplice in tutti gli scenari, perché ha esposizione media più bassa e quindi paga meno; con i costi però la differenza non è più distinguibile da zero. Con costi realistici nessuna delle due versioni lungo-corte ha un rendimento interessante nel periodo di test.

## 7. Limiti

- **Portafogli teorici.** I decili di French non hanno costi, vincoli allo scoperto né impatto di mercato. I costi sono solo scenari.
- **Volatilità dal file giornaliero.** Uso il WML giornaliero ricostituito ogni giorno, non i rendimenti giornalieri dei decili mensili come il paper. Sugli Sharpe della replica la differenza è piccola.
- **Sabati prima del 1952.** Fino a maggio 1952 la borsa era aperta anche il sabato (24,5 giorni al mese in media): 126 giorni sono circa cinque mesi e il fattore 21 sottostima la varianza mensile, quindi i pesi storici sono un po' più alti. Seguo la stessa convenzione del paper; nel test non conta.
- **Un solo periodo di test, con potenza limitata.** 176 mesi sono pochi per distinguere differenze di Sharpe dell'ordine di 0,1-0,2. Il limite inferiore a +0,003 va letto come un risultato al confine, non come una prova solida.
- **Leva senza tetto.** Nel campione storico il peso arriva a 2,09. Nel test non supera 1, ma in un periodo calmo la strategia userebbe leva.
- **Il momentum è stato più debole nel test.** Il WML semplice ha Sharpe 0,20 contro 0,54 del 1927-2011, ma con un errore standard della differenza di circa 0,28 non è significativa. È coerente con il calo delle anomalie dopo la pubblicazione (McLean e Pontiff 2016), ma questo progetto non lo dimostra.

## 8. Come riprodurre i numeri

Con Python 3.10 o successivo:

```
pip install -e ".[dev,dati,notebook]"
python scripts/00_scarica_dati.py             # oppure gli zip a mano in data/raw
python scripts/01_controlla_dati.py           # controlli sui dati
python scripts/02_replica_paper.py            # replica 1927-2011 -> docs/esito_replica.txt
python scripts/04_test_fuori_campione.py      # test 2012-2026 -> output/esito_test.txt
python scripts/05_analisi_dopo_il_test.py     # letture dopo il test -> docs/analisi_dopo_il_test.txt
python scripts/06_grafici.py                  # grafici in img/
python -m pytest -q                           # test (quelli sui dati reali solo se i dati ci sono)
```

Nella CI su GitHub i dati non ci sono, quindi lì girano solo i test sulle funzioni; i test sui dati reali (marcati `slow`) girano in locale.

`scripts/03_congela_configurazione.py` non va rilanciato: `config_congelata.json` esiste già e lo script si rifiuta di sovrascriverlo. Su una copia nuova il test si può rieseguire e deve dare lo stesso testo di `docs/esito_test.txt` (lo controlla anche `tests/test_dati_reali.py`). Il notebook [notebooks/risultati.ipynb](notebooks/risultati.ipynb) rilegge i risultati con le stesse funzioni.

## 9. Struttura del repository

```
src/risk_managed_momentum/
  dati.py            lettura degli zip di French (solo il primo blocco), WML, Mom dai 6 portafogli
  strategia.py       varianza prevista, peso, rendimento gestito
  serie.py           tutte le serie mensili usate dagli script
  misure.py          Sharpe, curtosi, drawdown, bootstrap stazionario, alfa con Newey-West
  costi.py           scenari di costo
  esame.py           verdetto e misure descrittive su una finestra di mesi
  configurazione.py  valori congelati del test e impronta dei criteri
  grafici.py         grafici del README e del notebook
scripts/             00-06, nell'ordine in cui vanno lanciati
tests/               test sulle funzioni e test sui dati reali (marcati slow)
docs/                criteri, esiti, metodo, domande e risposte
img/                 grafici
notebooks/           risultati.ipynb
config_congelata.json
```

## 10. Riferimenti

- Barroso, P. e Santa-Clara, P. (2015). Momentum has its moments. *Journal of Financial Economics*, 116(1), 111-120.
- Daniel, K. e Moskowitz, T. J. (2016). Momentum crashes. *Journal of Financial Economics*, 122(2), 221-247.
- Jegadeesh, N. e Titman, S. (1993). Returns to buying winners and selling losers. *Journal of Finance*, 48(1), 65-91.
- Moreira, A. e Muir, T. (2017). Volatility-managed portfolios. *Journal of Finance*, 72(4), 1611-1644.
- Cederburg, S., O'Doherty, M. S., Wang, F. e Yan, X. S. (2020). On the performance of volatility-managed portfolios. *Journal of Financial Economics*, 138(1), 95-117.
- McLean, R. D. e Pontiff, J. (2016). Does academic research destroy stock return predictability? *Journal of Finance*, 71(1), 5-32.
- Jobson, J. D. e Korkie, B. M. (1981). Performance hypothesis testing with the Sharpe and Treynor measures. *Journal of Finance*, 36(4), 889-908.
- Memmel, C. (2003). Performance hypothesis testing with the Sharpe ratio. *Finance Letters*, 1, 21-23.
- Lo, A. W. (2002). The statistics of Sharpe ratios. *Financial Analysts Journal*, 58(4), 36-52.
- Politis, D. N. e Romano, J. P. (1994). The stationary bootstrap. *Journal of the American Statistical Association*, 89(428), 1303-1313.
- Newey, W. K. e West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703-708.
- Kenneth R. French, Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
