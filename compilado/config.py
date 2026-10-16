"""Tudo que dá pra ajustar sem mexer no resto do código."""
from datetime import timedelta, timezone

# O Brasil não tem horário de verão desde 2019, então UTC-3 fixo resolve sem
# depender do tzdata (que o Python do Windows não traz).
FUSO = timezone(timedelta(hours=-3), "BRT")

# Feed de anúncios do dia do arXiv. cs.SE = Engenharia de Software, cs.PL = Linguagens de Programação.
ARXIV_CATEGORIAS = ["cs.SE", "cs.PL"]

# Hugging Face Daily Papers: os últimos HF_DIAS dias viram candidatos; a semana
# inteira só é usada na seção "Os mais votados da semana" (fim de semana, feriado).
HF_DIAS = 3
HF_DIAS_SEMANA = 7

# Quantos papers entram em cada parte do jornal.
LIMITES = {"alta": 3, "ia": 3, "se": 3, "pl": 2, "tambem": 8, "semana": 5}
MIN_DESTAQUES = 5        # abaixo disso a edição ganha "Os mais votados da semana"
VOTOS_EM_ALTA = 5        # votos no HF pra entrar em "Em alta na comunidade"
VOTOS_MANCHETE = 10      # abaixo disso a manchete sai do arXiv, pela nota
# Papers que só estão no HF precisam ser claramente de programação: assunto no título
# com relevância >= RELEVANCIA_MINIMA, ou relevância >= RELEVANCIA_SO_ABSTRACT só pelo abstract.
RELEVANCIA_MINIMA = 4
RELEVANCIA_SO_ABSTRACT = 10

ESQUECER_APOS_DIAS = 60  # depois disso um paper enviado pode voltar (na prática nunca volta)

ARQ_ESTADO = "dados/estado.json"
PASTA_EDICOES = "edicoes"
USER_AGENT = "o-compilado/1.0 (jornal pessoal de papers)"
