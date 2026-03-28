"""Script per estrarre risposte da un file Markdown basato su domande in un file Excel."""

import argparse
import pandas as pd
from rlm import RLM

def main():
    # Configurazione dei parametri da riga di comando
    parser = argparse.ArgumentParser(description="Estrae dati usando RLM partendo da un Markdown e un file Excel di domande.")
    parser.add_argument("--md_file", required=True, help="Percorso del file Markdown di input contenente il testo.")
    parser.add_argument("--excel_in", required=True, help="Percorso del file Excel/CSV contenente le domande e la Ground Truth.")
    parser.add_argument("--excel_out", default="risposte_modello.xlsx", help="Percorso del file Excel di output da generare.")
    args = parser.parse_args()

    # 1. Lettura del file Markdown
    print(f"📄 Lettura del file Markdown: {args.md_file}...")
    try:
        with open(args.md_file, "r", encoding="utf-8") as f:
            document = f.read()
    except Exception as e:
        print(f"❌ Errore nella lettura del file Markdown: {e}")
        return

    # 2. Lettura del file con le domande (supporta sia CSV che Excel)
    print(f"📊 Lettura delle domande da: {args.excel_in}...")
    try:
        if args.excel_in.endswith('.csv'):
            df_input = pd.read_csv(args.excel_in)
        else:
            df_input = pd.read_excel(args.excel_in)
            
        # Assicuriamoci che esista la colonna 'Domanda'
        if 'Domanda' not in df_input.columns:
            raise ValueError("Il file di input non contiene una colonna chiamata 'Domanda'.")
            
        # Rimuoviamo righe in cui la domanda è vuota
        df_input = df_input.dropna(subset=['Domanda'])
        # Convertiamo il dataframe in una lista di dizionari per iterare facilmente
        tasks_data = df_input.to_dict('records')
        print(f"✅ Trovate {len(tasks_data)} domande da elaborare.")
        
    except Exception as e:
        print(f"❌ Errore nella lettura del file delle domande: {e}")
        return

    # 3. Inizializzazione del modello RLM
    print("\n🤖 Inizializzazione del modello RLM...")
    rlm = RLM(
        model="ollama/qwen3.5:cloud",
        recursive_model="ollama/qwen3.5:4b",
        max_iterations=80,
        max_depth=4,
        temperature=0.1
    )

    rlm.repl.max_output_chars = 10_000

    # 4. Ciclo sequenziale sulle domande per generare le risposte
    risultati = []
    print("\n⏳ Inizio elaborazione...\n" + "=" * 80)
    
    for i, row in enumerate(tasks_data, 1):
        task = row['Domanda']
        # Recuperiamo Risposta e Pagina (se non esistono nel file di input, mettiamo stringa vuota)
        gt_risposta = row.get('Risposta', '')
        pagina = row.get('Pagina', '')

        print(f"\nDomanda {i}/{len(tasks_data)}: {task}")
        print("-" * 80)
        
        try:
            # Esecuzione del modello sul testo markdown
            result = rlm.complete(task, document)
            print(f"Risposta Generata:\n{result}")
        except Exception as e:
            result = f"ERRORE GENERAZIONE: {e}"
            print(f"❌ {result}")
            
        # Salva la riga completa per l'Excel finale rispettando l'ordine delle colonne
        risultati.append({
            "Domanda": task,
            "Risposta": gt_risposta,
            "Pagina": pagina,
            "Risposta Modello": result
        })

    # 5. Generazione del file Excel di output
    print("\n" + "=" * 80)
    print(f"💾 Salvataggio dei risultati in: {args.excel_out}...")
    try:
        # Il DataFrame creerà automaticamente le colonne nell'ordine in cui sono state inserite nel dizionario
        df_output = pd.DataFrame(risultati)
        df_output.to_excel(args.excel_out, index=False)
        print("✅ Salvataggio completato con successo!")
    except Exception as e:
        print(f"❌ Errore nel salvataggio del file Excel: {e}")

if __name__ == "__main__":
    main()