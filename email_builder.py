from datetime import datetime

from jinja2 import Template

from scraper import Article

TEMPLATE_HTML = Template("""\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Veille du {{ date }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8f9fa;
    color: #1a1a2e;
    padding: 16px;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.5;
  }
  .header {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    color: #fff;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 16px;
    text-align: center;
  }
  .header h1 { font-size: 20px; font-weight: 700; }
  .header .date { font-size: 13px; opacity: 0.8; margin-top: 4px; }
  .header .count { font-size: 13px; opacity: 0.7; margin-top: 2px; }
  .section {
    background: #fff;
    border-radius: 10px;
    margin-bottom: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .section-title {
    background: #e8eaf6;
    color: #1a1a2e;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .article {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
  }
  .article:last-child { border-bottom: none; }
  .article h3 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .article h3 a {
    color: #1a1a2e;
    text-decoration: none;
  }
  .article .resume {
    font-size: 13px;
    color: #555;
    margin-bottom: 6px;
  }
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 6px;
  }
  .tag {
    background: #e3f2fd;
    color: #1565c0;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
  }
  .definition {
    background: #fff8e1;
    border-left: 3px solid #ffc107;
    padding: 6px 10px;
    margin-top: 6px;
    border-radius: 0 6px 6px 0;
    font-size: 12px;
  }
  .definition strong {
    color: #e65100;
    text-transform: capitalize;
  }
  .source {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
  }
  .source a { color: #1565c0; }
  .footer {
    text-align: center;
    padding: 16px;
    font-size: 11px;
    color: #999;
  }
  .glossaire-section {
    background: #fff;
    border-radius: 10px;
    margin-bottom: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .glossaire-title {
    background: #fff3e0;
    color: #e65100;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
  }
  .glossaire-item {
    padding: 8px 16px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 13px;
  }
  .glossaire-item:last-child { border-bottom: none; }
  .glossaire-item strong { color: #e65100; }
</style>
</head>
<body>

<div class="header">
  <h1>Veille Actu</h1>
  <div class="date">{{ date }}</div>
  <div class="count">{{ total_articles }} articles &middot; {{ total_termes }} termes expliqués</div>
</div>

{% for categorie, articles in sections.items() %}
<div class="section">
  <div class="section-title">{{ categorie }}</div>
  {% for art in articles %}
  <div class="article">
    <h3><a href="{{ art.lien }}">{{ art.titre }}</a></h3>
    {% if art.resume %}
    <div class="resume">{{ art.resume }}</div>
    {% endif %}
    {% if art.mots_cles %}
    <div class="tags">
      {% for mc in art.mots_cles %}
      <span class="tag">{{ mc }}</span>
      {% endfor %}
    </div>
    {% endif %}
    {% for terme, defn in art.termes_definis.items() %}
    <div class="definition">
      <strong>{{ terme }}</strong> &mdash; {{ defn }}
    </div>
    {% endfor %}
    <div class="source">Source : <a href="{{ art.lien }}">Le Monde</a></div>
  </div>
  {% endfor %}
</div>
{% endfor %}

{% if tous_termes %}
<div class="glossaire-section">
  <div class="glossaire-title">Glossaire du jour</div>
  {% for terme, defn in tous_termes.items() %}
  <div class="glossaire-item">
    <strong>{{ terme }}</strong> &mdash; {{ defn }}
  </div>
  {% endfor %}
</div>
{% endif %}

<div class="footer">
  Généré automatiquement &middot; Sources : Le Monde (RSS)<br>
  Les résumés proviennent des flux RSS publics.
</div>

</body>
</html>
""")


def construire_email(sections: dict[str, list[Article]]) -> str:
    total_articles = sum(len(arts) for arts in sections.values())

    tous_termes: dict[str, str] = {}
    for articles in sections.values():
        for art in articles:
            tous_termes.update(art.termes_definis)

    return TEMPLATE_HTML.render(
        date=datetime.now().strftime("%A %d %B %Y").capitalize(),
        sections=sections,
        total_articles=total_articles,
        total_termes=len(tous_termes),
        tous_termes=tous_termes,
    )
