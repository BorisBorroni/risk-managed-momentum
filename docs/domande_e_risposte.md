# Domande e risposte

Risposte brevi alle domande che mi aspetto. I dettagli sono in [metodo.md](metodo.md).

**Che cosa hai fatto di tuo, se la strategia è di un paper?**
Ho scritto da zero il codice, l'ho controllato con la replica del paper e poi l'ho provato su 14 anni e 8 mesi che il paper non poteva vedere (2012-2026), con regole e criteri fissati prima. In più ho aggiunto i confronti (Mom di French, solo lungo, mercato), i costi e l'analisi dei crolli.

**Perché proprio questa strategia?**
Cercavo un effetto documentato su una storia lunga, con un meccanismo economico chiaro, dati gratuiti e regole già fissate dalla letteratura, così da non dover scegliere parametri guardando i risultati. Il momentum gestito per il rischio soddisfa tutti e quattro i criteri.

**Il risultato è positivo?**
Sul rischio sì: il drawdown passa da −64,8% a −23,0% e il mese peggiore da −32,1% a −12,5%. Una parte di questo calo viene solo dall'esposizione più bassa (vedi la domanda sulla pari volatilità). Sullo Sharpe la stima è positiva (+0,177) e l'intervallo al 95% è [+0,003; +0,333]: per la regola fissata prima è "evidenza", ma al limite. Il momentum in sé, invece, ha reso poco dopo il 2011.

**Perché lo Sharpe migliora se il peso medio è solo 0,50?**
Lo Sharpe non dipende dalla scala: dimezzare sempre il peso lascerebbe lo Sharpe uguale. Migliora perché il peso è basso proprio nei mesi in cui il momentum oscilla di più e, nel test, ha reso meno: il terzo dei mesi con la volatilità prevista più alta ha media annua −3,86%, gli altri due circa +10%. Con 59 mesi per gruppo, però, queste medie hanno errori standard di 8-16 punti, quindi la differenza tra i gruppi da sola non è significativa.

**Il gestito riduce il rischio solo perché investe meno?**
In parte sì. Se prendo il WML semplice e lo moltiplico per 0,423, in modo che abbia la stessa volatilità del gestito nel test (scelta fatta a posteriori, solo come confronto), il drawdown scende a −32,7% e il mese peggiore a −13,6%. Il gestito fa meglio: −23,0%, −12,5%, curtosi dimezzata (1,05 contro 2,10) e Sharpe 0,375 contro 0,197. Il contributo del "quando" ridurre il rischio è quindi reale, ma più piccolo di quello del confronto diretto, e sul mese peggiore è quasi nullo.

**Il peso usa informazioni future?**
No. Il peso del mese t usa i giorni fino alla fine del mese t−1. Tre test lo controllano: alterare i giorni del mese t non cambia il peso del mese t; troncare i dati non cambia i pesi passati; sui dati reali il peso di gennaio 2012 si calcola con i dati fino a dicembre 2011.

**Perché la replica non dà esattamente i numeri del paper?**
Il database CRSP viene rivisto nel tempo e io uso la versione 202608. In più stimo la volatilità con il file giornaliero di French, in cui i decili sono riformati ogni giorno, mentre il paper usa i giornalieri dei decili mensili. Le differenze sono piccole: Sharpe 0,54 contro 0,53 e 1,00 contro 0,97.

**Come fai a sapere che non hai guardato il test prima?**
Non posso dimostrarlo, è una mia dichiarazione. Il repository mostra che i criteri hanno un'impronta registrata in `config_congelata.json` e che lo script del test controlla l'impronta e non riparte nella stessa copia di lavoro. È una protezione contro gli errori, non una prova: chi clona il repository può rieseguire il test, e deve ottenere lo stesso testo di `docs/esito_test.txt`.

**Perché un bootstrap a blocchi e non un test t sulla differenza di Sharpe?**
I rendimenti del momentum hanno volatilità persistente e code pesanti, e le due serie sono molto correlate. Il bootstrap stazionario mantiene la dipendenza tra mesi vicini (blocchi di 6 mesi in media) e la correlazione tra le due serie (stessi indici), senza ipotesi di normalità.

**L'intervallo [+0,003; +0,333] è robusto?**
Solo in parte. Con altri semi resta positivo (limite inferiore tra +0,0003 e +0,0116), ma con blocchi medi di 1 o 3 mesi include lo zero, e il test di Jobson e Korkie con la correzione di Memmel dà p = 0,069. Per questo lo chiamo un risultato al limite. Il verdetto resta quello della regola fissata prima, ma non lo presento come una prova solida.

**E con i costi?**
Il gestito resta davanti al semplice in ogni scenario, ma la differenza non è più distinguibile da zero. Nello scenario medio il gestito ha Sharpe 0,19, nello scenario alto circa zero (0,00). Su questo periodo il momentum lungo-corto non sembra interessante al netto di costi realistici.

**Perché la versione lungo-corta come principale?**
È quella del paper, ed è dove la gestione del rischio dovrebbe agire: i crolli del momentum nascono soprattutto dalla gamba corta, quando i perdenti rimbalzano dopo un ribasso. Nel test quattro dei cinque mesi peggiori vengono dal rimbalzo dei perdenti, con il mercato in rialzo. Nel solo lungo, invece, la gestione dimezza volatilità e drawdown ma non cambia lo Sharpe (0,83 contro 0,84).

**C'è leva?**
Nel campione storico sì, il peso arriva a 2,09. Nel test no: il peso va da 0,18 a 0,99, perché la volatilità prevista del momentum è sempre stata sopra il 12%.

**Il gestito è solo il semplice con meno esposizione?**
No. Regredendo il gestito sul semplice l'alfa è del 2,33% annuo con t = 2,31 (errori di Newey e West), con beta 0,39. Una versione semplicemente ridotta avrebbe alfa zero.

**Conviene aggiungerlo a un portafoglio di mercato?**
Nel test, mercato più WML gestito ha Sharpe 1,11 contro 0,94 e drawdown −18,8% contro −25,3%. La differenza di Sharpe però ha intervallo [−0,173; +0,468]: non è distinguibile da zero, ed è prima dei costi.

**Il momentum funziona ancora?**
In questo periodo poco: Sharpe 0,20 contro 0,54 del 1927-2011. Con un errore standard della differenza di circa 0,28, però, non è significativa: è coerente con il calo delle anomalie dopo la pubblicazione (McLean e Pontiff 2016), ma non lo dimostra. Il miglioramento della gestione del rischio si vede soprattutto nel 2016-2026, quando il momentum semplice ha avuto i crolli peggiori.

**Che cosa cambieresti con più tempo?**
Userei i rendimenti giornalieri dei decili mensili come nel paper (servono i dati CRSP a livello di titolo, non gratuiti). Stimerei il turnover vero per avere costi meno ipotetici. Proverei la stessa regola su mercati diversi dagli Stati Uniti come seconda verifica fuori campione.
