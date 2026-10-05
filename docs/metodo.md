# Metodo: dettagli tecnici

Questo documento raccoglie i dettagli che nel README sono solo accennati. I termini (WML, *winners minus losers*, Sharpe, drawdown, curtosi, bootstrap e gli altri) sono spiegati nel [glossario del README](../README.md#11-glossario). I numeri citati vengono da [esito_replica.txt](esito_replica.txt), [esito_test.txt](esito_test.txt) e [analisi_dopo_il_test.txt](analisi_dopo_il_test.txt).

## 1. Lettura dei dati

Ogni zip di French contiene un CSV con più blocchi uno sotto l'altro: rendimenti pesati per capitalizzazione, pesati in modo uguale, annuali, numero di imprese. `dati.leggi_testo` legge solo il primo blocco. Il blocco comincia alla riga di intestazione, quella che inizia con una virgola, e finisce alla prima riga che non comincia con una data di 6 cifre (AAAAMM) o di 8 cifre (AAAAMMGG). Nei file usati il primo blocco è sempre quello pesato per capitalizzazione. La funzione si ferma con un errore se trova valori mancanti (−99,99 o −999), righe con un numero di colonne sbagliato o date non crescenti. I valori sono in percento e diventano rendimenti decimali; le date mensili diventano la fine del mese.

Controlli in `scripts/01_controlla_dati.py`:

- nessun valore mancante e nessun mese saltato;
- mensili da 1927-01 a 2026-08 (1.196 mesi), giornalieri dal 1926-11-03 al 2026-08-31 (26.216 giorni), gli stessi giorni nei quattro file giornalieri;
- fattore Mom ricostruito dai 6 portafogli come 0,5 × (vincenti piccoli + vincenti grandi) − 0,5 × (perdenti piccoli + perdenti grandi): differenza massima 0,01 punti percentuali, sia mensile sia giornaliero, cioè l'arrotondamento dei file;
- mercato mensile (Mkt-RF + RF) contro il composto dei giornalieri dello stesso mese: 1 mese su 1.201 differisce di più di 0,2 punti (settembre 1931, 0,40 punti).

Lo script stampa anche il calendario. Gli unici due intervalli lunghi tra giorni di borsa sono la chiusura delle banche del marzo 1933 (12 giorni tra due sedute) e la chiusura dopo l'11 settembre 2001 (7 giorni tra due sedute). Fino al 24 maggio 1952 si contrattava anche il sabato (1.142 sabati): in quel periodo un mese ha in media 24,5 giorni di borsa, da giugno 1952 21,0.

## 2. La regola

Per ogni mese t:

- σ²(t) = 21 × (1/126) × Σ r²(d), con la somma sugli ultimi 126 rendimenti giornalieri di WML fino all'ultimo giorno di borsa del mese t−1. Come nel paper, la media dei quadrati non toglie la media: su sei mesi di dati giornalieri la media è trascurabile rispetto alla varianza.
- σ annua (t) = √(12 × σ²(t)).
- peso(t) = 0,12 / σ annua (t).
- rendimento gestito(t) = peso(t) × WML(t).

Il primo mese con 126 giorni precedenti è maggio 1927, quindi replica e confronti partono da lì. Il fattore 21 e i 126 giorni sono quelli del paper anche per gli anni con il sabato: fino al 1952 la finestra copre circa cinque mesi e la varianza mensile è sottostimata di circa il 14% (21/24,5 ≈ 0,86), quindi i pesi storici sono più alti di circa l'8%. Nel periodo di test non c'è differenza. In `strategia.varianza_prevista` la media mobile dei quadrati è presa all'ultimo giorno di ogni mese e assegnata al mese successivo. Che non ci siano dati futuri lo controllano tre test automatici in `tests/`: alterare i giorni di un mese non cambia il peso di quel mese; troncare i dati alla fine di un mese non cambia nessun peso passato; sui dati reali, il peso di gennaio 2012 è già noto con i dati fino a dicembre 2011.

**Differenza dal paper.** Il paper stima la varianza con i rendimenti giornalieri dei decili formati ogni mese. Io uso il file giornaliero di French, in cui i decili sono riformati ogni giorno (rendimento passato da −250 a −21 giorni). È l'unica fonte giornaliera gratuita; gli Sharpe della replica restano comunque vicini al paper (1,00 contro 0,97), mentre sulle code del gestito la distanza è più ampia (curtosi 2,00 contro 2,68); non ho verificato quanto dipenda da questa scelta.

**Altre serie gestite.** La stessa regola si applica al fattore Mom (varianza dal Mom giornaliero) e al decile vincente solo lungo (varianza da decile vincente giornaliero meno RF giornaliero).

## 3. Misure

Su rendimenti mensili in eccesso:

- media annua = 12 × media mensile; volatilità annua = deviazione standard (ddof = 1) × √12; Sharpe = media / deviazione standard × √12;
- asimmetria = m3 / m2^1,5 e curtosi in eccesso = m4 / m2² − 3, con i momenti centrali della popolazione;
- drawdown massimo sul capitale composto 1 × Π(1 + r), con il capitale iniziale come primo massimo. Per il lungo-corto è il capitale di chi tiene la liquidità al tasso privo di rischio e aggiunge la strategia: il drawdown riguarda la parte in eccesso;
- alfa: regressione mensile gestito = α + β × semplice + errore, con errori standard di Newey e West (6 ritardi); α annuo = 12 × α mensile.

Le convenzioni su curtosi e drawdown sono state scritte nei criteri prima del test. La scelta conta poco: nella replica la curtosi corretta per il campione sarebbe 18,04 invece di 17,95 per il semplice e 2,01 invece di 2,00 per il gestito.

## 4. Bootstrap stazionario

Per l'intervallo della differenza di Sharpe uso il bootstrap stazionario di Politis e Romano (1994):

1. ogni ricampionamento è una sequenza di 176 mesi fatta di blocchi di mesi consecutivi (circolari);
2. a ogni passo si comincia un blocco nuovo da un mese a caso con probabilità 1/6, altrimenti si prende il mese successivo: i blocchi hanno lunghezza geometrica con media 6 mesi;
3. le due serie (gestita e semplice) sono ricampionate con gli **stessi indici**, così la loro forte correlazione resta;
4. 10.000 ricampionamenti, seme 0; intervallo al 95% dai percentili 2,5% e 97,5% delle differenze.

I blocchi servono perché la volatilità del momentum è persistente: ricampionare mesi singoli romperebbe questa dipendenza.

**Sensibilità (calcolata dopo il test).** Con 20 semi diversi il limite inferiore resta tra +0,0003 e +0,0116. Con blocco medio 1 l'intervallo è [−0,026; +0,360], con 3 è [−0,006; +0,348], con 12 è [+0,023; +0,312], con 24 è [+0,044; +0,298]. La conclusione "tutto sopra lo zero" dipende quindi dalla lunghezza dei blocchi, ed è per questo che nel README la chiamo un'evidenza al limite.

**Controllo con un test classico (dopo il test).** Il test di Jobson e Korkie con la correzione di Memmel (2003), che assume rendimenti indipendenti e normali, dà z = 1,82 e p = 0,069. La correlazione tra le due serie è 0,93: è per questo che una differenza di Sharpe di 0,18 si può quasi distinguere da zero anche in soli 176 mesi.

**Rendimento della strategia contro zero.** Sul test il t della media (media / errore standard, senza correzioni) è circa 0,76 per il semplice e 1,43 per il gestito: nessuno dei due è distinguibile da zero.

## 5. Costi

I file di French non contengono il turnover, quindi i costi sono ipotesi. Per un peso w (w = 1 per le strategie non gestite), ogni mese:

- prestito titoli: tasso annuo / 12 × nozionale corto (w per il lungo-corto, 0 per il solo lungo);
- negoziazione: tasso annuo / 12 × esposizione lorda (2w per il lungo-corto, w per il solo lungo). Rappresenta il ribilanciamento mensile dei decili, i cui titoli cambiano ogni mese;
- variazione del peso: costo per lato × esposizione scambiata (2 × |Δw| per il lungo-corto, |Δw| per il solo lungo). Il primo mese non la paga.

| Scenario | Prestito | Negoziazione | Variazione del peso |
|---|---|---|---|
| lordo | 0% | 0% | 0 pb |
| medio | 0,5% | 2% | 10 pb |
| alto | 1% | 4% | 20 pb |

Il costo della variazione del peso è una precisazione che ho aggiunto ai criteri dopo la replica e prima del test: il piano iniziale lo nominava senza dare un valore. Nel test il WML semplice perde circa 4,5 punti all'anno nello scenario medio e 9 nello scenario alto; il gestito circa la metà, perché il peso medio è 0,50.

## 6. Analisi dopo il test

`scripts/05_analisi_dopo_il_test.py` (eseguito dopo il test, non cambia il verdetto):

- **Meccanismo.** Correlazione della volatilità prevista con la volatilità realizzata nel mese dopo (dai giornalieri dello stesso mese): +0,74 nel 1927-2011, +0,65 nel test. Correlazione con il rendimento del WML: −0,12 (t −3,9) nel 1927-2011 e −0,14 (t −1,9) nel test. Dividendo i mesi del test in tre gruppi in base al peso, il terzo con peso più basso (volatilità prevista più alta) ha media annua −3,86% con volatilità 34,74%; gli altri due hanno medie di 10,70% e 10,34% con volatilità 31,82% e 17,45%. Gli errori standard delle medie sono però grandi (15,7%, 14,5% e 7,9%), quindi nel test la differenza tra i gruppi non è significativa. Il quadro è coerente con l'idea del paper (il rendimento non sale con la volatilità, quindi scalare migliora lo Sharpe), che sul campione lungo è più netta.
- **Pari volatilità.** Il WML semplice moltiplicato per una costante (0,423, scelta a posteriori perché abbia la stessa volatilità del gestito nel test) ha drawdown −32,71%, mese peggiore −13,57%, curtosi 2,10 e Sharpe 0,197. Il gestito ha −23,03%, −12,52%, 1,05 e 0,375. Due delle tre misure dell'ipotesi 1 (drawdown e mese peggiore) migliorano anche solo riducendo l'esposizione; quello che resta dopo questo confronto è il contributo del "quando" ridurre l'esposizione: circa 10 punti di drawdown, metà della curtosi e lo Sharpe, mentre sul mese peggiore il contributo è quasi nullo. L'ipotesi 1 era scritta contro il WML semplice e il verdetto resta quello, ma questa è la lettura più corretta.
- **Crolli.** Nei 5 mesi peggiori del semplice il peso era tra 0,20 e 0,39 (tabella nella [sezione 7.3 del README](../README.md#73-dove-nasce-il-miglioramento)). In quattro mesi su cinque i perdenti salgono molto più dei vincenti (fino a +46,75% ad aprile 2020); a luglio 2026, invece, sono i vincenti a crollare (−15,41%).
- **Bootstrap.** Sensibilità a semi e lunghezza dei blocchi (sezione 4 di questo documento).

## 7. Collegamento con la letteratura

- Barroso e Santa-Clara (2015) mostrano che il rischio del momentum è molto variabile e prevedibile; scalare per la volatilità porta lo Sharpe da 0,53 a 0,97 nel 1927-2011.
- Daniel e Moskowitz (2016) spiegano i crolli: dopo un ribasso forte, quando il mercato rimbalza, i perdenti (spesso titoli ad alto beta) salgono molto più dei vincenti. Nel test quattro dei cinque mesi peggiori hanno il mercato in rialzo, ma solo due (aprile 2020 e gennaio 2023) arrivano dopo 24 mesi di mercato in calo, e di poco: il quadro è coerente con il loro meccanismo, non una conferma.
- Moreira e Muir (2017) estendono l'idea a molti fattori. Cederburg e coautori (2020) mostrano che, applicate in tempo reale, le versioni gestite per la volatilità non battono in modo sistematico gli originali. Per questo un test fuori campione su una strategia ben precisa ha senso: qui il risultato è un miglioramento forte sul rischio e un miglioramento dello Sharpe positivo ma statisticamente al limite.
- McLean e Pontiff (2016): dopo la pubblicazione i rendimenti delle anomalie calano. Il WML semplice passa da Sharpe 0,54 (1927-2011) a 0,20 (2012-2026), ma con un errore standard della differenza di circa 0,28 (0,26 nel test, 0,11 nel 1927-2011, formula di Lo con rendimenti indipendenti, che con code pesanti è ottimistica) la differenza non è significativa; inoltre il momentum è stato pubblicato nel 1993, quindi anche il campione 1927-2011 contiene anni successivi alla pubblicazione.
