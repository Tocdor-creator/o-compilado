"""Escolhe os principais papers do dia e distribui pelas seções do jornal.

Paper recém-saído não tem citação, então a nota usa o que dá pra saber no dia:
quanto o texto é sobre programação, votos no Hugging Face, se tem código
publicado e se já foi aceito em alguma conferência/revista.
"""
import math
import re

from .config import (
    LIMITES, MIN_DESTAQUES, RELEVANCIA_MINIMA, RELEVANCIA_SO_ABSTRACT, VOTOS_EM_ALTA, VOTOS_MANCHETE,
)

# (padrão, peso). Cada padrão conta uma vez; no título vale o dobro.
TERMOS = [(re.compile(p, re.I), peso) for p, peso in [
    (r"\bcod(e|ing)[- ](generation|llms?|models?|agents?|review|completion|search|repair|reasoning|editing|translation|intelligence)\b", 4),
    (r"\bcoding (agents?|assistants?|tasks?|benchmarks?)\b|\bsoftware agents?\b|\bswe-?bench\w*|\bswe[- ]agents?\b", 4),
    (r"\bsoftware (engineering|development|testing|maintenance|vulnerabilit\w+|repositor\w+|supply chain)\b", 4),
    (r"\bprogram (synthesis|repair|analysis|verification|comprehension|generation)\b", 4),
    (r"\bprogramming languages?\b|\bcompil(er|ers|ation)\b|\btype (systems?|checking|inference)\b", 4),
    (r"\btest(s|ing)? generation\b|\btest (cases?|suites?)\b|\bfuzz(ing|ers?)?\b|\bstatic analysis\b|\brefactor\w*", 3),
    (r"\bsource code\b|\bcodebases?\b|\brepositor(y|ies)[- ]level\b|\bpull requests?\b|\bterminal(-bench| agents?)\b", 3),
    (r"\bbugs?\b|\bdebug\w*|\bvulnerability detection\b|\bformal verification\b|\bsmart contracts?\b", 2),
    (r"\bcode\b|\bcoding\b|\bprogram(s|ming)?\b|\bsoftware\b|\bdevelopers?\b|\bcommits?\b", 1),
    (r"\b(text-to-sql|sql|python|rust|javascript|typescript|webassembly|cuda|gpu kernels?|apis?)\b", 1),
]]
RE_IA = re.compile(
    r"\b(llms?|large language models?|language models?|agents?|agentic|neural|deep learning"
    r"|transformers?|gpt[-\w]*|reinforcement learning|foundation models?)\b",
    re.I,
)
RE_SIGLA_LM = re.compile(r"[A-Za-z]*LMs?\b")  # LLM, VLM, CodeLMs... sem re.I, senão casa "films"
SECOES = [("ia", "IA aplicada ao código"), ("se", "Engenharia de Software"), ("pl", "Linguagens & Compiladores")]


def relevancia(p):
    n = 0
    for padrao, peso in TERMOS:
        if padrao.search(p["titulo"]):
            n += 2 * peso
        elif padrao.search(p["resumo"]):
            n += peso
    return n


def sobre_programacao(p):
    """Pra papers que só estão no HF (IA em geral). Muito paper de LLM cita "code reasoning"
    de passagem no abstract, então o assunto tem que estar no título, ou dominar o abstract."""
    rel = relevancia(p)
    no_titulo = any(padrao.search(p["titulo"]) for padrao, _ in TERMOS)
    return (no_titulo and rel >= RELEVANCIA_MINIMA) or rel >= RELEVANCIA_SO_ABSTRACT


def nota(p):
    n = relevancia(p)
    if p.get("periodico"):
        n += 3
    if p.get("codigo"):
        n += 2
    if p.get("votos"):
        n += 3 * math.log2(1 + p["votos"])
    return n


def secao(p):
    cats = p["categorias"]
    if (cats and cats[0] in ("cs.PL", "cs.LO")) or ("cs.PL" in cats and "cs.SE" not in cats):
        return "pl"
    texto = p["titulo"] + " " + p["resumo"]
    if RE_IA.search(texto) or RE_SIGLA_LM.search(texto):
        return "ia"
    return "se"


def _junta(arxiv, hf):
    """Paper que está nas duas fontes vira um só: texto do arXiv + votos, resumo e código do HF."""
    por_id = {p["id"]: dict(p) for p in arxiv}
    for h in hf:
        p = por_id.get(h["id"])
        if p is None:
            por_id[h["id"]] = dict(h)
            continue
        for campo in ("votos", "tldr", "estrelas", "org", "data_hf"):
            p[campo] = h[campo]
        p["codigo"] = p["codigo"] or h["codigo"]
    return list(por_id.values())


def _votos(p):
    return p.get("votos") or 0


def monta(arxiv, hf_recentes, hf_semana, enviados):
    pool = [
        p for p in _junta(arxiv, hf_recentes)
        if p["id"] not in enviados and (p["fonte"] == "arxiv" or sobre_programacao(p))
    ]
    for p in pool:
        p["nota"] = nota(p)
        p["secao"] = secao(p)
    pool.sort(key=lambda p: p["nota"], reverse=True)

    em_alta = sorted((p for p in pool if _votos(p) >= VOTOS_EM_ALTA), key=_votos, reverse=True)
    if em_alta and _votos(em_alta[0]) >= VOTOS_MANCHETE:
        manchete = em_alta[0]
    else:
        manchete = pool[0] if pool else None
    usados = {manchete["id"]} if manchete else set()

    def pega(candidatos, limite):
        escolhidos = [p for p in candidatos if p["id"] not in usados][:limite]
        usados.update(p["id"] for p in escolhidos)
        return escolhidos

    alta = pega(em_alta, LIMITES["alta"])
    # As seções seguem as categorias do arXiv; o que só está no HF já teve a chance em "Em alta".
    secoes = [
        (titulo, pega([p for p in pool if p["fonte"] == "arxiv" and p["secao"] == chave], LIMITES[chave]))
        for chave, titulo in SECOES
    ]
    tambem = pega(pool, LIMITES["tambem"])

    destaques = bool(manchete) + len(alta) + sum(len(ps) for _, ps in secoes)
    semana = []
    if destaques < MIN_DESTAQUES:
        semana = sorted(
            (h for h in hf_semana if h["id"] not in usados and sobre_programacao(h)),
            key=_votos, reverse=True,
        )[:LIMITES["semana"]]

    return {
        "manchete": manchete,
        "alta": alta,
        "secoes": [(t, ps) for t, ps in secoes if ps],
        "tambem": tambem,
        "semana": semana,
        "analisados": len(arxiv) + len(hf_recentes),
    }


def papers_da_edicao(edicao):
    """Os que contam como já enviados (a retrospectiva da semana não conta)."""
    ps = [edicao["manchete"]] if edicao["manchete"] else []
    ps += edicao["alta"] + [p for _, lista in edicao["secoes"] for p in lista] + edicao["tambem"]
    return ps
