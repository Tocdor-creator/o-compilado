"""Resumo sem IA: escolhe, no próprio abstract, as frases que dizem o que o paper
faz e o que ele encontrou. Abstract de paper é bem previsível ("We propose...",
"Results show..."), então algumas expressões regulares já acertam a maioria.
"""
import re

ABREVIACOES = re.compile(r"\b(e\.g|i\.e|et al|etc|vs|cf|Fig|Eq|Sec|approx|resp)\.", re.I)
CONTRIBUICAO = re.compile(
    r"\b(we (propose|present|introduce|develop|design|build|describe|study|investigate|conduct|perform"
    r"|explore|formali[sz]e|implement|report|analy[sz]e|evaluate|release|curate|construct|identify)"
    r"|this (paper|work|article|study)|in this (paper|work)"
    r"|our (approach|method|tool|framework|technique|system|study|work))\b",
    re.I,
)
RESULTADO = re.compile(
    r"\b(results? (show|demonstrate|indicate|reveal|suggest)|we (show|find|found|observe|demonstrate)"
    r"|outperform\w*|achiev\w*|improv\w*|reduc\w*|speed-?ups?|surpass\w*|state-of-the-art|found that)\b",
    re.I,
)
NUMERO = re.compile(r"\d+(\.\d+)?\s?(%|x\b|×|times\b)")


def frases(texto):
    t = re.sub(r"\s+", " ", texto or "").strip()
    t = ABREVIACOES.sub(lambda m: m.group(0).replace(".", "\x00"), t)
    partes = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])", t)
    return [p.replace("\x00", ".").strip() for p in partes if p.strip()]


def _nota_resultado(f):
    return len(RESULTADO.findall(f)) + 2 * bool(NUMERO.search(f))


def resumo(abstract, max_chars=700):
    """Até três frases: o contexto (se couber), a contribuição e o principal resultado."""
    fs = frases(abstract)
    if len(fs) <= 3:
        return " ".join(fs)
    contrib = next((i for i, f in enumerate(fs) if CONTRIBUICAO.search(f)), None)
    if contrib is None:
        contrib = 1 if len(fs[0]) < 120 else 0  # sem pista: a 1ª frase, ou a 2ª se a 1ª for só um gancho curto
    notas = [(_nota_resultado(f), -i, i) for i, f in enumerate(fs) if i > contrib]
    resultado = max(notas)[2] if notas and max(notas)[0] > 0 else None

    escolhidas = [contrib] + ([resultado] if resultado is not None else [])
    if contrib > 0:
        com_contexto = [0] + escolhidas
        if sum(len(fs[i]) for i in com_contexto) <= max_chars:
            escolhidas = com_contexto
    return " ".join(fs[i] for i in escolhidas)


def linha(abstract, max_chars=200):
    """Uma linha só, pra lista "Também nesta edição"."""
    fs = frases(abstract)
    if not fs:
        return ""
    f = next((f for f in fs if CONTRIBUICAO.search(f)), fs[0])
    if len(f) <= max_chars:
        return f
    return f[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "…"
