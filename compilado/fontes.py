"""Coleta: feed de anúncios do arXiv e Daily Papers do Hugging Face.

Cada fonte devolve papers no mesmo formato (dict), pra o resto do código não
precisar saber de onde veio cada um.
"""
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta

from .config import ARXIV_CATEGORIAS, USER_AGENT

NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
RE_REPO = re.compile(r"https?://(?:www\.)?(?:github|gitlab)\.com/[\w.-]+/[\w.-]+")


def _baixa(url, tentativas=4):
    espera = 5
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            # 4xx (fora o 429 de "devagar") não melhora tentando de novo
            if isinstance(e, urllib.error.HTTPError) and e.code != 429 and e.code < 500:
                raise
            if i == tentativas - 1:
                raise
            time.sleep(espera)
            espera *= 3


def _limpa(t):
    return re.sub(r"\s+", " ", t or "").strip()


def _repo(texto):
    m = RE_REPO.search(texto or "")
    return m.group(0).rstrip(".") if m else None


def _paper(id_, **campos):
    p = {
        "id": id_, "titulo": "", "autores": [], "resumo": "", "categorias": [],
        "link": f"https://arxiv.org/abs/{id_}", "pdf": f"https://arxiv.org/pdf/{id_}",
        "fonte": "arxiv", "votos": None, "tldr": None, "codigo": None, "estrelas": None,
        "org": None, "periodico": None, "tipo": None, "data_hf": None,
    }
    p.update(campos)
    return p


def _autores_arxiv(texto):
    # "Fulana (USP, Unicamp), Beltrano (MIT)": separa nas vírgulas fora dos parênteses
    nomes = re.split(r",\s*(?![^()]*\))", _limpa(texto))
    return [re.sub(r"\s*\(.*?\)", "", n).strip() for n in nomes if n.strip()]


def arxiv():
    """Papers anunciados na última leva do arXiv (sai por volta das 21h de Brasília, dom-qui)."""
    raiz = ET.fromstring(_baixa("https://rss.arxiv.org/atom/" + "+".join(ARXIV_CATEGORIAS)))
    papers = []
    for e in raiz.findall("a:entry", NS):
        tipo = _limpa(e.findtext("arxiv:announce_type", "", NS))
        if tipo not in ("new", "cross"):  # "replace" é versão nova de paper antigo
            continue
        id_ = re.sub(r"v\d+$", "", _limpa(e.findtext("a:id", "", NS)).rsplit(":", 1)[-1])
        resumo = _limpa(re.sub(r"^.*?Abstract:", "", e.findtext("a:summary", "", NS), flags=re.S))
        papers.append(_paper(
            id_,
            titulo=_limpa(e.findtext("a:title", "", NS)),
            autores=_autores_arxiv(e.findtext("{http://purl.org/dc/elements/1.1/}creator", "")),
            resumo=resumo,
            categorias=[c.get("term") for c in e.findall("a:category", NS)],
            codigo=_repo(resumo),
            periodico=_limpa(e.findtext("arxiv:journal_reference", "", NS)) or None,
            tipo=tipo,
        ))
    return papers


def hugging_face(hoje, dias):
    """Daily Papers dos últimos `dias` dias. Um paper que aparece em mais de um dia fica com o maior número de votos."""
    por_id, erros = {}, []
    for n in range(dias):
        data = hoje - timedelta(days=n)
        try:
            itens = json.loads(_baixa(f"https://huggingface.co/api/daily_papers?date={data:%Y-%m-%d}&limit=100"))
        except Exception as e:  # um dia fora do ar não derruba a edição
            erros.append(f"{data:%d/%m}: {e}")
            continue
        for item in itens:
            h = item["paper"]
            votos = int(h.get("upvotes") or 0)
            if h["id"] in por_id and por_id[h["id"]]["votos"] >= votos:
                continue
            org = h.get("organization") or item.get("organization") or {}
            por_id[h["id"]] = _paper(
                h["id"],
                titulo=_limpa(h.get("title")),
                autores=[a["name"] for a in h.get("authors", []) if not a.get("hidden") and a.get("name")],
                resumo=_limpa(h.get("summary")),
                fonte="hf",
                votos=votos,
                tldr=_limpa(h.get("ai_summary")) or None,
                codigo=h.get("githubRepo") or _repo(h.get("summary")),
                estrelas=h.get("githubStars"),
                org=org.get("fullname"),
                data_hf=data.isoformat(),
            )
    return list(por_id.values()), erros
