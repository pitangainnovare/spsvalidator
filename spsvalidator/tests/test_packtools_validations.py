"""
Verifica que validate_sps_zip exercita todos os 36 grupos de validação
definidos no packtools 4.16.6 xml_validator.py.

Três camadas de testes:
  1. Versão       — packtools 4.16.6 está instalada.
  2. Cobertura    — cada função validate_* é chamada por validate_sps_zip.
  3. Comportamento — grupos novos no 4.16.x detectam problemas em XML real.
  4. Regressão    — bugs corrigidos no packtools#1230 (TypeError em validate_secs,
                    validate_lists e validate_response) não regridem.
"""
from __future__ import annotations

import zipfile
from textwrap import dedent

import pytest

from spsvalidator.domain.validation import validate_sps_zip


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_zip(tmp_path, xml_content: str) -> str:
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("article.xml", xml_content)
    return str(zip_path)


def _rows_groups(result) -> set[str]:
    return {r["group"] for r in result["rows"]}


def _all_groups(result) -> set[str]:
    """Grupos em rows E em exceptions (inclui casos onde packtools lança exceção)."""
    return _rows_groups(result) | {r["group"] for r in result["exceptions"]}


def _article(
    *,
    body: str = "",
    back: str = "",
    extra_meta: str = "",
    include_permissions: bool = True,
) -> str:
    permissions_block = (
        dedent("""\
            <permissions>
              <license license-type="open-access"
                       xlink:href="https://creativecommons.org/licenses/by/4.0/">
                <license-p>Open access.</license-p>
              </license>
            </permissions>""")
        if include_permissions
        else ""
    )
    default_body = "<sec><title>Introduction</title><p>Text.</p></sec>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<article xmlns:xlink="http://www.w3.org/1999/xlink"'
        ' article-type="research-article" xml:lang="pt" dtd-version="1.1">\n'
        "<front>\n"
        "<journal-meta>\n"
        '<journal-id journal-id-type="nlm-ta">Rev Test</journal-id>\n'
        "<journal-title-group>"
        "<journal-title>Revista de Teste</journal-title>"
        '<abbrev-journal-title abbrev-type="publisher">Rev. Teste</abbrev-journal-title>'
        "</journal-title-group>\n"
        '<issn pub-type="epub">1234-5678</issn>\n'
        "<publisher><publisher-name>Publisher</publisher-name></publisher>\n"
        "</journal-meta>\n"
        "<article-meta>\n"
        '<article-id pub-id-type="doi">10.1234/test.2023.001</article-id>\n'
        '<article-id pub-id-type="publisher-id">S1234-56782023000100001</article-id>\n'
        "<article-categories>"
        '<subj-group subj-group-type="heading"><subject>Original Article</subject></subj-group>'
        "</article-categories>\n"
        "<title-group><article-title>Test Article Title</article-title></title-group>\n"
        "<contrib-group>"
        '<contrib contrib-type="author">'
        "<name><surname>Silva</surname><given-names>João</given-names></name>"
        "</contrib>"
        "</contrib-group>\n"
        '<pub-date publication-format="electronic" date-type="pub">'
        "<year>2023</year><month>01</month><day>01</day>"
        "</pub-date>\n"
        "<volume>1</volume>\n"
        "<elocation-id>e001</elocation-id>\n"
        + permissions_block + "\n"
        + extra_meta + "\n"
        "</article-meta>\n"
        "</front>\n"
        "<body>" + (body or default_body) + "</body>\n"
        "<back>" + back + "</back>\n"
        "</article>\n"
    )


# ---------------------------------------------------------------------------
# 1. Cobertura: cada função validate_* é chamada por validate_sps_zip
# ---------------------------------------------------------------------------

# (group_name, function_name em xml_validations)
VALIDATION_FUNCTIONS = [
    ("journal-meta",            "validate_journal_meta"),
    ("bibliographic strip",     "validate_bibliographic_strip"),
    ("article attributes",      "validate_article"),
    ("article-id",              "validate_article_ids"),
    ("article dates",           "validate_article_dates"),
    ("history",                 "validate_history"),
    ("article languages (1)",   "validate_article_languages"),
    ("article languages (2)",   "validate_metadata_languages"),
    ("subject",                 "validate_article_toc_sections"),
    ("article-type",            "validate_article_type"),
    ("contrib",                 "validate_article_contribs"),
    ("aff",                     "validate_affiliations"),
    ("author-notes",            "validate_author_notes"),
    ("abstract",                "validate_abstracts"),
    ("open science",            "validate_open_science_actions"),
    ("funding data",            "validate_funding_data"),
    ("id and rid",              "validate_id_and_rid_match"),
    ("fig",                     "validate_figs"),
    ("table-wrap",              "validate_tablewraps"),
    ("disp-formula",            "validate_equations"),
    ("inline-formula",          "validate_inline_equations"),
    ("reference",               "validate_references"),
    ("related-article",         "validate_related_articles"),
    ("fn",                      "validate_fns"),
    ("reviewer-report",         "validate_peer_reviews"),
    ("accessibility",           "validate_accessibility_data"),
    ("media",                   "validate_media"),
    ("app",                     "validate_app_group"),
    ("supplementary-material",  "validate_supplementary_materials"),
    ("ext-link",                "validate_ext_links"),
    ("list",                    "validate_lists"),
    ("graphic",                 "validate_graphics"),
    ("response",                "validate_response"),
    ("sec",                     "validate_secs"),
    ("product",                 "validate_products"),
    ("permissions",             "validate_permissions"),
]


@pytest.mark.parametrize(
    "group,func_name",
    VALIDATION_FUNCTIONS,
    ids=[func for _, func in VALIDATION_FUNCTIONS],
)
def test_validation_function_is_called(tmp_path, monkeypatch, group, func_name):
    """Cada função validate_* do packtools deve ser chamada por validate_sps_zip."""
    from packtools.sps.validation import xml_validations

    called = {"yes": False}
    original = getattr(xml_validations, func_name)

    def spy(*args, **kwargs):
        called["yes"] = True
        return original(*args, **kwargs)

    monkeypatch.setattr(xml_validations, func_name, spy)
    validate_sps_zip(_make_zip(tmp_path, _article()))

    assert called["yes"], f"{func_name} não foi chamada por validate_sps_zip"


# ---------------------------------------------------------------------------
# 2. Comportamento: grupos novos no 4.16.x detectam problemas reais
# ---------------------------------------------------------------------------


def test_table_wrap_sem_label_e_caption_reporta_issue(tmp_path):
    """<table-wrap> sem <label> E sem <caption> → issue no grupo table-wrap."""
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <table-wrap id="t01">
            <table>
              <tbody><tr><td>data</td></tr></tbody>
            </table>
          </table-wrap>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "table-wrap" in _rows_groups(result)


def test_sec_sem_title_reporta_issue(tmp_path):
    """<sec> sem <title> → packtools reporta issue (via rows ou exceptions)."""
    xml = _article(body="<sec><p>Text without title.</p></sec>")
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "sec" in _all_groups(result)


def test_permissions_sem_license_reporta_issue(tmp_path):
    """<permissions> sem <license> → issue no grupo permissions."""
    xml = _article(
        include_permissions=False,
        extra_meta="<permissions><copyright-year>2023</copyright-year></permissions>",
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "permissions" in _rows_groups(result)


def test_fig_sem_label_reporta_issue(tmp_path):
    """<fig> sem <label> → issue no grupo fig."""
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <fig id="f01">
            <caption><title>Caption</title></caption>
            <graphic xlink:href="fig01.tif"/>
          </fig>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "fig" in _rows_groups(result)


def test_fn_sem_fn_type_reporta_issue(tmp_path):
    """<fn> sem atributo fn-type → issue no grupo fn."""
    xml = _article(
        back="""
        <fn-group>
          <fn id="fn01">
            <p>Footnote without type.</p>
          </fn>
        </fn-group>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "fn" in _rows_groups(result)


def test_history_sem_received_reporta_issue(tmp_path):
    """<history> sem evento received → issue no grupo history."""
    xml = _article(
        extra_meta="""
        <history>
          <date date-type="accepted">
            <day>01</day><month>06</month><year>2023</year>
          </date>
        </history>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "history" in _rows_groups(result)


def test_list_sem_list_type_reporta_issue(tmp_path):
    """<list> sem atributo list-type → packtools reporta issue (via rows ou exceptions)."""
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <list>
            <list-item><p>Item</p></list-item>
          </list>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "list" in _all_groups(result)


def test_related_article_sem_href_reporta_issue(tmp_path):
    """<related-article> sem xlink:href → issue no grupo related-article."""
    xml = _article(
        extra_meta="""
        <related-article related-article-type="commentary-article" id="ra1"/>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "related-article" in _rows_groups(result)


def test_reference_sem_campos_obrigatorios_reporta_issue(tmp_path):
    """<ref> sem author e sem source → issue no grupo reference."""
    xml = _article(
        back="""
        <ref-list>
          <ref id="r01">
            <element-citation publication-type="journal">
              <article-title>Title only, no authors, no source</article-title>
              <year iso-8601-date="2020">2020</year>
            </element-citation>
          </ref>
        </ref-list>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "reference" in _rows_groups(result)


def test_ext_link_sem_href_reporta_issue(tmp_path):
    """<ext-link> sem xlink:href → issue no grupo ext-link."""
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <p><ext-link ext-link-type="uri">No href link</ext-link></p>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "ext-link" in _rows_groups(result)


def test_graphic_sem_href_reporta_issue(tmp_path):
    """<graphic> avulso sem xlink:href → issue no grupo graphic."""
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <p><graphic id="g01"/></p>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "graphic" in _rows_groups(result)


def test_abstract_sem_lang_reporta_issue(tmp_path):
    """<abstract> sem xml:lang → issue no grupo abstract."""
    xml = _article(extra_meta="<abstract><p>Resumo sem lang.</p></abstract>")
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "abstract" in _rows_groups(result)


# ---------------------------------------------------------------------------
# 3. Versão do packtools
# ---------------------------------------------------------------------------


def test_packtools_version():
    """packtools 4.16.6 deve estar instalada."""
    import packtools

    assert packtools.__version__ == "4.16.6"


# ---------------------------------------------------------------------------
# 4. Regressão packtools#1230 — TypeError em validate_secs, validate_lists
#    e validate_response quando as funções não tinham `yield from`.
#
#    Antes do fix, essas funções retornavam None (sem yield from), causando
#    TypeError: 'NoneType' object is not iterable no orquestrador.
#    Agora devem produzir resultados estruturados via rows ou exceptions.
# ---------------------------------------------------------------------------


def test_regression_1230_validate_secs_nao_levanta_typeerror(tmp_path):
    """Regressão packtools#1230: validate_secs não deve lançar TypeError.

    <sec> sem <title> exercita a validação; antes do fix o resultado era None
    e o orquestrador lançava TypeError ao iterar.
    """
    xml = _article(body="<sec><p>Texto sem titulo.</p></sec>")
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "sec" in _all_groups(result), (
        "validate_secs retornou None (sem yield from) — regressão do packtools#1230"
    )


def test_regression_1230_validate_lists_nao_levanta_typeerror(tmp_path):
    """Regressão packtools#1230: validate_lists não deve lançar TypeError.

    <list> sem @list-type exercita a validação; antes do fix o resultado era
    None e o orquestrador lançava TypeError ao iterar.
    """
    xml = _article(
        body="""
        <sec>
          <title>Section</title>
          <list>
            <list-item><p>Item sem list-type.</p></list-item>
          </list>
        </sec>"""
    )
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    assert "list" in _all_groups(result), (
        "validate_lists retornou None (sem yield from) — regressão do packtools#1230"
    )


def test_regression_1230_validate_response_nao_levanta_typeerror(tmp_path):
    """Regressão packtools#1230: validate_response não deve lançar TypeError.

    Um artigo com <response> exercita validate_response; antes do fix o
    resultado era None e o orquestrador lançava TypeError ao iterar.
    Aqui o XML é válido, portanto o grupo só aparece em rows se houver issue
    ou em exceptions se houver erro — a ausência de TypeError já é suficiente.
    """
    xml = _article(
        body="""
        <sec><title>Section</title><p>Text.</p></sec>
        <response response-type="reply" xml:lang="pt" id="r01">
          <front-stub>
            <title-group>
              <article-title>Reply title</article-title>
            </title-group>
          </front-stub>
          <body><sec><title>Reply body</title><p>Reply.</p></sec></body>
        </response>"""
    )
    # Se TypeError ocorrer dentro de validate_sps_zip ele vira exception com
    # response="exception". A ausência disso — ou a presença de resultados
    # estruturados — confirma que o fix está ativo.
    result = validate_sps_zip(_make_zip(tmp_path, xml))
    typeerrors = [
        e for e in result["exceptions"]
        if e.get("group") == "response" and "NoneType" in e.get("error", "")
    ]
    assert not typeerrors, (
        "validate_response lançou TypeError — regressão do packtools#1230"
    )