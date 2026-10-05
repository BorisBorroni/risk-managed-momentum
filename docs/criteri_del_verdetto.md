# Criteri del verdetto

Scritti prima di calcolare qualsiasi rendimento del periodo di test (gennaio 2012 - agosto 2026). Il repository non può provare la data in cui li ho scritti, quindi è una mia dichiarazione; lo script del test controlla però che questo file non sia cambiato rispetto a `config_congelata.json` e si rifiuta di ripartire se l'esito esiste già.

## Strategia (identica al paper di Barroso e Santa-Clara 2015)

- WML = decile vincente meno decile perdente (10 decili sul rendimento da t-12 a t-2, pesati per capitalizzazione), file mensile. È autofinanziata, quindi è già un rendimento in eccesso.
- Varianza prevista per il mese t: 21 × media dei quadrati degli ultimi 126 rendimenti giornalieri di WML fino all'ultimo giorno di borsa del mese t-1. Volatilità annua = radice di 12 volte la varianza mensile.
- Peso del mese t = 12% / volatilità prevista, senza tetto (nel paper i pesi vanno da 0,13 a 2,00).
- WML giornaliero per la varianza: decile vincente meno decile perdente dal file giornaliero. Differenza dichiarata: il file giornaliero è ricostituito ogni giorno, mentre il paper usa i rendimenti giornalieri dei decili mensili.

## Fasi

1. Replica sul periodo del paper (1927-2011): è una verifica del codice, non un risultato. Accettazione: Sharpe del semplice e del gestito entro ±0,10 da 0,53 e 0,97. Esito in [esito_replica.txt](esito_replica.txt).
2. Test fuori campione: gennaio 2012 - agosto 2026 (176 mesi), dopo la fine dei dati del paper. Il sottoperiodo dopo la pubblicazione (dal 2016) è solo descrittivo.

## Ipotesi e regola di decisione (test 2012-2026)

- **Ipotesi 1, rischio.** Il WML gestito ha drawdown massimo, mese peggiore e curtosi in eccesso più bassi del WML semplice. Confermata solo se migliorano tutte e tre.
- **Ipotesi 2, misura primaria.** Differenza di Sharpe (gestito meno semplice), con intervallo al 95% da bootstrap stazionario sui mesi (blocco medio di 6 mesi, 10.000 ricampionamenti, stessi indici per le due serie).
  - Evidenza di miglioramento: intervallo tutto sopra lo zero.
  - Indicazione debole: stima positiva, ma intervallo che include lo zero.
  - Nessun miglioramento: stima uguale o inferiore a zero.

## Misure descrittive (non entrano nel verdetto)

- Alfa del gestito sul semplice (regressione mensile, errori di Newey e West con 6 ritardi).
- Sottoperiodi 2012-2015 e 2016-2026.
- Confronti: fattore Mom di French (semplice e gestito, robustezza), decile vincente solo lungo in eccesso su RF (semplice e gestito), mercato (Mkt-RF), mercato più WML gestito in sovrapposizione.

## Costi (ipotesi esplicite: i file di French non contengono il turnover)

Tre scenari, riportati accanto ai risultati lordi:

| Scenario | Prestito titoli (annuo, sul nozionale corto) | Negoziazione (annua, per unità di esposizione lorda) | Variazione del peso (per lato, su 2 × \|Δpeso\|) |
|---|---|---|---|
| lordo | 0% | 0% | 0 punti base |
| medio | 0,5% | 2% | 10 punti base |
| alto | 1% | 4% | 20 punti base |

Per la strategia lungo-corta con peso w il nozionale corto è w e l'esposizione lorda è 2w; per il solo lungo non c'è prestito, l'esposizione lorda è w e la variazione del peso si paga su \|Δpeso\|.

## Precisazioni scritte prima del test

- Curtosi in eccesso e asimmetria dai momenti centrali della popolazione (m4/m2² − 3, m3/m2^1,5).
- Drawdown massimo sul capitale composto dei rendimenti mensili in eccesso, con il capitale iniziale come primo massimo.
- Sharpe annuo = media mensile / deviazione standard mensile × radice di 12.
- Intervallo del bootstrap a percentili (2,5% e 97,5%), seme fisso 0.
- Il costo della variazione del peso (ultima colonna della tabella dei costi) è una precisazione aggiunta al piano dopo la replica e prima del test.

## Limiti già noti

- Portafogli teorici: niente vincoli allo scoperto, niente impatto di mercato.
- WML giornaliero ricostituito ogni giorno usato solo per stimare la varianza.
- Leva fino a circa 2 volte senza tetto, come nel paper.
- Un solo periodo di test (176 mesi): potenza limitata sulla differenza di Sharpe.
