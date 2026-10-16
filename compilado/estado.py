"""O que já foi enviado. Fica num JSON versionado no próprio repositório: o
GitHub Actions faz commit dele depois de cada edição, e é assim que os
agendamentos reserva sabem que a edição do dia já saiu."""
import json
import os
from datetime import date, timedelta

from .config import ARQ_ESTADO, ESQUECER_APOS_DIAS


def carrega():
    try:
        with open(ARQ_ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"numero": 0, "ultima_edicao": None, "enviados": {}}


def registra(estado, hoje, papers):
    estado["numero"] += 1
    estado["ultima_edicao"] = hoje.isoformat()
    for p in papers:
        estado["enviados"][p["id"]] = hoje.isoformat()
    limite = (hoje - timedelta(days=ESQUECER_APOS_DIAS)).isoformat()
    estado["enviados"] = {i: d for i, d in estado["enviados"].items() if d >= limite}


def salva(estado):
    os.makedirs(os.path.dirname(ARQ_ESTADO), exist_ok=True)
    with open(ARQ_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def ja_saiu_hoje(estado, hoje: date):
    return estado.get("ultima_edicao") == hoje.isoformat()
