# utils/rag_engine.py
# RAG simple et robuste pour RegIntel AI : RAG d'abord, LLM en secours.

from pathlib import Path
from typing import List, Dict, Tuple
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME, EMBEDDING_MODEL, TOP_K_RESULTS

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / ".chroma"
CHROMA_DIR.mkdir(exist_ok=True)


class RAGEngine:
    """
    Moteur RAG pour RegIntel AI.
    - Utilise Chroma en mode persistant (.chroma)
    - Utilise OpenAI pour les embeddings + LLM
    - Essaie TOUJOURS d'utiliser le RAG si des documents sont indexés.
    - Ne filtre pas agressivement sur les distances (pour éviter de rater BCBS).
    """

    def __init__(self, collection_name: str = "regintel_local") -> None:
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name=EMBEDDING_MODEL,
            ),
        )

    # --------- maintenance ---------
    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def stats(self) -> Dict:
        return {
            "path": str(CHROMA_DIR),
            "collection": self.collection.name,
            "count": self.count(),
        }

    def add_documents(self, chunks: List[Dict]) -> None:
        if not chunks:
            return
        docs = [c["text"] for c in chunks]
        metas = [c["metadata"] for c in chunks]
        ids = [f'{m["source"]}-{m["chunk"]}' for m in metas]
        self.collection.add(documents=docs, metadatas=metas, ids=ids)

    def clear_collection(self) -> None:
        try:
            self.chroma.delete_collection(self.collection.name)
        except Exception:
            pass
        self.collection = self.chroma.get_or_create_collection(
            name=self.collection.name,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name=EMBEDDING_MODEL,
            ),
        )

    # --------- requête publique ---------
    def answer(self, question: str, prefer_rag: bool = True, answer_mode: str = "Auto") -> Dict:
        """
        Retourne :
        {
          "answer": str,
          "sources": List[str],  # pour affichage dans l'UI
          "mode": "RAG" | "LLM"
        }

        answer_mode ∈ {"Auto", "Overview", "Gap analysis", "Remediation plan"}
        """
        has_vectors = self.count() > 0

        # Si pas de docs → LLM direct
        if not has_vectors or not prefer_rag:
            return self._llm_only(question, answer_mode=answer_mode)

        # Essayer le RAG
        rag_result = self._rag_answer(question, answer_mode=answer_mode)
        if rag_result.get("sources"):
            return rag_result

        # Si le RAG n'a rien de vraiment exploitable → fallback LLM
        return self._llm_only(question, answer_mode=answer_mode)
    
    def _is_bcbs_principles_query(self, question: str) -> bool:
        """True si la question demande explicitement les principes BCBS 239."""
        q = (question or "").lower()
        has_bcbs = any(k in q for k in ["bcbs 239", "bcbs239", "risk data aggregation"])
        has_principle = any(k in q for k in ["principle", "principe", "principes"])
        return has_bcbs and has_principle


    # --------- coeur RAG ---------
    def _rag_answer(self, question: str, answer_mode: str = "Auto") -> Dict:
        # Large top-N pour avoir de la matière
        N = max(30, TOP_K_RESULTS * 4)

        res = self.collection.query(
            query_texts=[question],
            n_results=N,
            include=["documents", "metadatas", "distances"],
        )

        docs = res.get("documents", [[]])[0] or []
        metas = res.get("metadatas", [[]])[0] or []
        dists = res.get("distances", [[]])[0] or []

        triples: List[Tuple[str, Dict, float]] = list(zip(docs, metas, dists))
        if not triples:
            return {
                "answer": "Insufficient evidence in RAG store.",
                "sources": [],
                "mode": "RAG",
            }

        # --- détecter une question type "présente les principes de BCBS 239" ---
        bcbs_mode = self._is_bcbs_principles_query(question)

        # 1) Prioriser les sources BCBS / RDARR / rapport SSM
        def priority(meta: Dict) -> int:
            src = (meta.get("source") or "").lower()
            if "bcbs239" in src and "report" not in src:
                return 0  # texte officiel BCBS239
            if "rdarr" in src:
                return 1
            if "bcbs_239_report" in src or "bcbs_239" in src:
                return 2
            return 5  # autres docs

        triples.sort(key=lambda t: (priority(t[1]), t[2]))

        selected: List[Tuple[str, Dict, float]] = []

        # ---------- CHEMIN SPÉCIAL BCBS 239 ----------
        if bcbs_mode:
            bcbs_triples: List[Tuple[str, Dict, float]] = []

            # On tente de récupérer tous les documents de la collection
            try:
                all_items = self.collection.get()
            except Exception:
                all_items = None

            if all_items is not None:
                docs_all = all_items.get("documents") or []
                metas_all = all_items.get("metadatas") or []
                for d, m in zip(docs_all, metas_all):
                    m = m or {}
                    src = (m.get("source") or "").lower()
                    if "bcbs239" in src:
                        bcbs_triples.append((d, m, 0.0))

            # Si pour une raison quelconque on n'a rien trouvé, on fallback sur triples
            if not bcbs_triples:
                bcbs_triples = [
                    t for t in triples
                    if "bcbs239" in (t[1].get("source") or "").lower()
                ]

            if bcbs_triples:
                # On ordonne par numéro de chunk pour avoir l'ordre 1→14
                bcbs_triples.sort(key=lambda t: t[1].get("chunk", 0))
                # On garde large : tous les principes + un peu de contexte
                selected = bcbs_triples[:60]
            else:
                # Si toujours rien, on désactive le mode spécial et on passera au chemin générique
                bcbs_mode = False

        # ---------- FIN CHEMIN SPÉCIAL BCBS 239 ----------

        # 2) Chemin générique : limiter le nombre de chunks par document
        if not bcbs_mode:
            MAX_PER_SOURCE = 4
            MAX_TOTAL = min(len(triples), TOP_K_RESULTS * 3)

            buckets = {}
            selected = []
            for doc, meta, dist in triples:
                src = meta.get("source", "unknown")
                cnt = buckets.get(src, 0)
                if cnt >= MAX_PER_SOURCE:
                    continue
                buckets[src] = cnt + 1
                selected.append((doc, meta, dist))
                if len(selected) >= MAX_TOTAL:
                    break

        if not selected:
            return {
                "answer": "Insufficient evidence in RAG store.",
                "sources": [],
                "mode": "RAG",
            }

        # 3) Construire les extraits de preuves (snippets courts)
        evidence_lines = []
        flat_sources = []
        for i, (doc, meta, dist) in enumerate(selected, 1):
            src = meta.get("source", "unknown")
            ch = meta.get("chunk", "?")
            # extrait court (≈ 280 caractères)
            text = (doc or "").replace("\n", " ").strip()
            snippet = text[:280] + ("…" if len(text) > 280 else "")
            evidence_lines.append(f"[{i}] {src} — chunk {ch}\n{snippet}")
            flat_sources.append(f"[{i}] {src} — chunk {ch}\n{snippet}")

        evidence_text = "\n\n".join(evidence_lines)

        # Instructions liées au mode
        mode_instruction = ""
        am = (answer_mode or "Auto").lower()
        if am == "overview":
            mode_instruction = (
                "- Donne une synthèse structurée et pédagogique (titres courts, liste numérotée) "
                "des exigences réglementaires mentionnées dans l'EVIDENCE.\n"
            )
        elif am == "gap analysis":
            mode_instruction = (
                "- Fais une analyse d'écart entre les exigences réglementaires et les pratiques "
                "décrites par l'utilisateur (si elles sont mentionnées dans la question). "
                "Structure ta réponse en: forces, gaps, recommandations.\n"
            )
        elif am == "remediation plan":
            mode_instruction = (
                "- Propose un plan de remédiation pragmatique et séquencé (court terme, moyen terme, "
                "long terme) basé sur l'EVIDENCE. Priorise les quick wins.\n"
            )

        # 4) Prompt : laisser le modèle adapter le format à la question
        prompt = f"""
Tu es RegIntel AI, copilote de conformité pour les banques européennes.
Tu dois répondre UNIQUEMENT à partir des extraits ci-dessous (EVIDENCE).
Si les éléments sont partiels, tu donnes une réponse partielle et tu l'indiques clairement.

Règles :
- Réponds dans la langue de la question.
- Si la question est une présentation (ex: "présente les principes de BCBS 239"),
  fais une synthèse structurée (liste numérotée, titres courts).
- Si la question parle de comparaison / gap / écart, fais une analyse de gap
  (points de convergence, écarts, recommandations).
{mode_instruction}- NE PAS inventer d’articles ou de principes qui ne sont pas visibles dans l’EVIDENCE.
- Si l’EVIDENCE est insuffisante pour répondre correctement, dis-le explicitement.

QUESTION UTILISATEUR :
{question}

EVIDENCE (à citer avec [#]) :
{evidence_text}
"""

        resp = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant de conformité bancaire. "
                        "Tes réponses doivent être courtes, précises et fondées sur les preuves fournies."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        answer_text = resp.choices[0].message.content

        return {
            "answer": answer_text,
            "sources": flat_sources,
            "mode": "RAG",
        }


    # --------- fallback LLM (sans RAG) ---------
    def _llm_only(self, question: str, answer_mode: str = "Auto") -> Dict:
        q_low = question.lower()

        # Si le user discute juste ("ça va ?", "who are you?")
        smalltalk_triggers = ["ça va", "tu vas bien", "how are you", "who are you"]
        if any(t in q_low for t in smalltalk_triggers):
            txt = (
                "Je suis RegIntel AI, un copilote de conformité pour les banques. "
                "Je n’ai pas d’émotions, mais je suis prêt à t’aider sur les sujets "
                "de réglementation, de gestion des risques et de conformité. "
                "Pose-moi une question sur un règlement (BCBS 239, RDARR, EU AI Act, etc.) "
                "ou partage un document pour que je l’analyse."
            )
            return {"answer": txt, "sources": [], "mode": "LLM"}

        sys_msg = (
            "Tu es RegIntel AI, copilote de conformité bancaire. "
            "Réponds dans la langue de l'utilisateur. "
            "Adapte le style de la réponse au mode demandé "
            f"(mode actuel: {answer_mode}). "
            "Si la question est purement réglementaire générale (sans documents), "
            "tu peux t'appuyer sur tes connaissances générales mais reste factuel et concis. "
            "Rappelle si nécessaire que tu n'es pas un conseiller juridique."
        )

        resp = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
        )

        return {
            "answer": resp.choices[0].message.content,
            "sources": [],
            "mode": "LLM",
        }
