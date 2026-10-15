import os
import pandas as pd

def anonymize_volunteer_sheet(input_path="data/xlsx/Voluntarios_20261015.xlsx", output_path="data/xlsx/Voluntarios_anonimizado.xlsx"):
    if not os.path.exists(input_path):
        print(f"Arquivo original não encontrado em: {input_path}")
        return

    print(f"Lendo planilha original: {input_path}")
    df = pd.read_excel(input_path, sheet_name="Voluntarios")

    # Anonimiza o CPF/Documento mascarando os dígitos centrais
    def mask_doc(doc):
        doc_str = str(doc).strip()
        if len(doc_str) >= 11:
            return f"***.{doc_str[4:7]}.{doc_str[8:11]}-**"
        return "***.***.***-**"

    if "Documento" in df.columns:
        df["Documento"] = df["Documento"].apply(mask_doc)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_excel(output_path, sheet_name="Voluntarios", index=False)
    print(f"Planilha anonimizada gerada com sucesso em: {output_path}")

if __name__ == "__main__":
    anonymize_volunteer_sheet()