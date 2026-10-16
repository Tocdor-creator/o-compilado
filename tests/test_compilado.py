import unittest
from datetime import date

from compilado import estado, jornal, ranking, resumo
from compilado.fontes import _autores_arxiv, _paper

ABSTRACT = (
    "Large codebases are hard to navigate, e.g. for new developers. Existing tools only index symbols. "
    "In this paper, we propose RepoMap, a tool that builds a navigable map of a repository. "
    "We describe its design in Sec. 3. We evaluate RepoMap on 40 open-source projects. "
    "Results show that RepoMap reduces onboarding time by 37% compared to grep-based search."
)


def paper(id_="2610.00001", titulo="RepoMap: Mapping Codebases", resumo=ABSTRACT, **campos):
    campos.setdefault("categorias", ["cs.SE"])
    return _paper(id_, titulo=titulo, resumo=resumo, autores=["Ana Lima"], **campos)


class Resumo(unittest.TestCase):
    def test_nao_quebra_frase_em_abreviacao(self):
        fs = resumo.frases(ABSTRACT)
        self.assertEqual(fs[0], "Large codebases are hard to navigate, e.g. for new developers.")
        self.assertIn("We describe its design in Sec. 3.", fs)

    def test_pega_contexto_contribuicao_e_resultado(self):
        r = resumo.resumo(ABSTRACT)
        self.assertTrue(r.startswith("Large codebases"))
        self.assertIn("we propose RepoMap", r)
        self.assertTrue(r.endswith("grep-based search."))
        self.assertNotIn("Sec. 3", r)

    def test_abstract_curto_vai_inteiro(self):
        self.assertEqual(resumo.resumo("One. Two."), "One. Two.")

    def test_linha_corta_na_palavra(self):
        l = resumo.linha("In this paper we propose " + "a very long idea " * 30, 80)
        self.assertTrue(l.endswith("…"))
        self.assertLessEqual(len(l), 81)


class Ranking(unittest.TestCase):
    def test_paper_de_ia_que_so_cita_codigo_no_abstract_fica_de_fora(self):
        p = paper(titulo="Waypoint: Policy Shifts via On-Policy Distillation",
                  resumo="We improve math and code reasoning benchmarks.", fonte="hf", votos=400)
        self.assertFalse(ranking.sobre_programacao(p))

    def test_paper_de_coding_agent_entra(self):
        p = paper(titulo="SWE-Duel: A Self-Scaling Arena for Coding Agents", fonte="hf", votos=20)
        self.assertTrue(ranking.sobre_programacao(p))

    def test_secoes(self):
        self.assertEqual(ranking.secao(paper(categorias=["cs.PL"])), "pl")
        self.assertEqual(ranking.secao(paper(resumo="We study CodeLMs.")), "ia")
        self.assertEqual(ranking.secao(paper(resumo="We study build systems.")), "se")
        self.assertEqual(ranking.secao(paper(resumo="We study films.")), "se")

    def test_monta_junta_fontes_e_nao_repete_enviados(self):
        arxiv = [paper("1"), paper("2", titulo="Type inference for Python"), paper("3")]
        hf = [paper("1", fonte="hf", votos=50, tldr="Mapa do repositório."),
              paper("9", titulo="Code generation with agents", fonte="hf", votos=30)]
        ed = ranking.monta(arxiv, hf, hf, enviados={"3": "2026-10-15"})
        self.assertEqual(ed["manchete"]["id"], "1")
        self.assertEqual(ed["manchete"]["tldr"], "Mapa do repositório.")
        ids = [p["id"] for p in ranking.papers_da_edicao(ed)]
        self.assertEqual(sorted(ids), ["1", "2", "9"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_dia_fraco_ganha_retrospectiva(self):
        semana = [paper(str(i), titulo=f"Coding agents {i}", fonte="hf", votos=i) for i in range(10)]
        ed = ranking.monta([], [], semana, enviados={})
        self.assertEqual([p["votos"] for p in ed["semana"]], [9, 8, 7, 6, 5])


class Jornal(unittest.TestCase):
    def test_renderiza_e_escapa(self):
        ed = ranking.monta([paper(titulo="Fast <script> & Safe")], [], [], {})
        assunto, html, texto = jornal.renderiza(ed, 7, date(2026, 10, 16), "08:00")
        self.assertIn("O Compilado nº 7 · 16/10", assunto)
        self.assertIn("sexta-feira, 16 de outubro de 2026", html)
        self.assertIn("Fast &lt;script&gt; &amp; Safe", html)
        self.assertNotIn("<script>", html)
        self.assertIn("https://arxiv.org/abs/2610.00001", texto)

    def test_edicao_vazia(self):
        ed = ranking.monta([], [], [], {})
        assunto, html, _ = jornal.renderiza(ed, 1, date(2026, 10, 17), "08:00")
        self.assertIn("sem papers novos", assunto)
        self.assertIn("Nenhum paper novo", html)


class Diversos(unittest.TestCase):
    def test_autores_com_afiliacao(self):
        self.assertEqual(_autores_arxiv("Ana (USP, Unicamp), Bia (MIT)"), ["Ana", "Bia"])

    def test_estado_registra_e_esquece_antigos(self):
        est = {"numero": 3, "ultima_edicao": None, "enviados": {"velho": "2026-01-01"}}
        estado.registra(est, date(2026, 10, 16), [paper("novo")])
        self.assertEqual(est["numero"], 4)
        self.assertTrue(estado.ja_saiu_hoje(est, date(2026, 10, 16)))
        self.assertEqual(est["enviados"], {"novo": "2026-10-16"})


if __name__ == "__main__":
    unittest.main()
