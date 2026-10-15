import os
import difflib
import unicodedata
import pandas as pd

class VolunteerCatalog:
    DE_PARA_LIVROS = {
        "MANUTENCAO PREVENTIVA": "2 - LIVRO Nº 2 - C43 - MANUTENÇÃO PREVENTIVA",
        "MANUTENÇÃO": "2 - LIVRO Nº 2 - C43 - MANUTENÇÃO PREVENTIVA",
        "ADMINISTRATIVO": "4 - LIVRO Nº 4 - C45 - ADMINISTRATIVO",
        "ALMOXARIFADO": "4 - LIVRO Nº 4 - C45 - ALMOXARIFADO PIEDADE",
        "COSTURA": "4 - LIVRO Nº 4 - C45 - COSTURA",
        "COZINHA": "4 - LIVRO Nº 4 - C45 - COZINHA",
        "GARAGEM": "4 - LIVRO Nº 4 - C45 - GARAGEM",
        "LIMPEZA": "4 - LIVRO Nº 4 - C45 - LIMPEZA",
    }

    STOPWORDS = {"DE", "DA", "DO", "DOS", "DAS", "E"}

    def __init__(self, excel_path=os.path.join("data", "xlsx", "Voluntarios_20261015.xlsx")):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Planilha não encontrada em: {excel_path}")

        self.df = pd.read_excel(excel_path, sheet_name="Voluntarios")
        self.df["Voluntário"] = self.df["Voluntário"].astype(str).str.strip().str.upper()
        self.df["Status"] = self.df["Status"].astype(str).str.strip()

        self.df_ativos = self.df[self.df["Status"].str.upper() == "ATIVO"].copy()
        self.nomes_ativos = self.df_ativos["Voluntário"].tolist()
        self.nomes_todos = self.df["Voluntário"].tolist()

    @staticmethod
    def _normalize(text):
        text = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("ASCII")
        return text.upper().replace(".", " ").strip()

    @staticmethod
    def _seq_ratio(a, b):
        return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

    def _smart_volunteer_score(self, query, choice):
        q_norm = self._normalize(query)
        c_norm = self._normalize(choice)

        q_raw_tokens = [t for t in q_norm.split() if t not in self.STOPWORDS]
        c_tokens = [t for t in c_norm.split() if t not in self.STOPWORDS]

        if not q_raw_tokens or not c_tokens:
            return 0.0

        # Expande abreviações manuscritas comuns ("Ma." -> MARIA, "Ap." -> APARECIDA)
        q_tokens = []
        for i, t in enumerate(q_raw_tokens):
            if i == 0 and t in ["MA", "M"]:
                q_tokens.append("MARIA")
            elif t == "AP":
                q_tokens.append("APARECIDA")
            else:
                q_tokens.append(t)

        # 1. Similaridade do primeiro nome (trata casos como "Amabile" -> "ANA BETE")
        first_sim = self._seq_ratio(q_tokens[0], c_tokens[0])
        if len(c_tokens) >= 2:
            first_sim = max(first_sim, self._seq_ratio(q_tokens[0], c_tokens[0] + c_tokens[1]))

        # 2. Similaridade do sobrenome final
        if len(q_tokens) >= 2:
            last_sim = max(
                self._seq_ratio(q_tokens[-1], c_tokens[-1]),
                max(self._seq_ratio(q_tokens[-1], ct) for ct in c_tokens[1:])
            )
        else:
            last_sim = first_sim

        # 3. Melhor casamento para cada parte do nome (tratando iniciais de 1 letra como "G" ou "M")
        token_scores = []
        for qt in q_tokens:
            if len(qt) == 1:
                abv_match = max([100.0 if ct.startswith(qt) else 0.0 for ct in c_tokens])
                token_scores.append(abv_match)
            else:
                best_t = max([self._seq_ratio(qt, ct) for ct in c_tokens])
                if len(c_tokens) >= 2:
                    best_t = max(best_t, self._seq_ratio(qt, c_tokens[0] + c_tokens[1]))
                token_scores.append(best_t)

        avg_token_score = sum(token_scores) / len(token_scores)
        full_sim = self._seq_ratio(" ".join(q_tokens), " ".join(c_tokens))

        return (0.35 * first_sim) + (0.20 * last_sim) + (0.30 * avg_token_score) + (0.15 * full_sim)

    def get_names_for_prompt(self, only_active=True):
        nomes = self.nomes_ativos if only_active else self.nomes_todos
        return "\n".join([f"- {nome}" for nome in sorted(nomes)])

    def match_volunteer(self, candidate_name, min_score=65.0):
        if not candidate_name or not candidate_name.strip():
            return None

        # Busca prioritária nos voluntários ATIVOS
        scored_ativos = [(self._smart_volunteer_score(candidate_name, name), name) for name in self.nomes_ativos]
        scored_ativos.sort(reverse=True)
        best_score, best_name = scored_ativos[0]

        if best_score >= min_score:
            row = self.df_ativos[self.df_ativos["Voluntário"] == best_name].iloc[0]
            return {
                "codigo": int(row["Código"]),
                "nome_oficial": best_name,
                "status": row["Status"],
                "score": round(best_score, 1)
            }

        # Fallback na lista completa (Incluindo Inativos)
        scored_todos = [(self._smart_volunteer_score(candidate_name, name), name) for name in self.nomes_todos]
        scored_todos.sort(reverse=True)
        best_score_all, best_name_all = scored_todos[0]

        if best_score_all >= min_score:
            row = self.df[self.df["Voluntário"] == best_name_all].iloc[0]
            return {
                "codigo": int(row["Código"]),
                "nome_oficial": best_name_all,
                "status": row["Status"],
                "score": round(best_score_all, 1)
            }

        return {
            "codigo": None,
            "nome_oficial": candidate_name.strip().upper(),
            "status": "NÃO ENCONTRADO",
            "score": round(best_score_all, 1)
        }

    def resolve_book_name(self, raw_activity):
        if not raw_activity:
            return "LIVRO NÃO IDENTIFICADO"
        q_norm = self._normalize(raw_activity)
        scored = [(self._seq_ratio(q_norm, k), v) for k, v in self.DE_PARA_LIVROS.items()]
        scored.sort(reverse=True)
        if scored[0][0] >= 55.0:
            return scored[0][1]
        return f"VERIFICAR MANUALMENTE ({raw_activity})"