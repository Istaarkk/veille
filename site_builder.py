import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment

from analyse import Brief
from config import REGIONS
from scraper import Article

PARIS = ZoneInfo("Europe/Paris")

TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#14161c">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Veille">
<meta name="robots" content="noindex">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon.svg">
<title>Veille</title>
<style>
:root {
  --bg: #f4f3ef; --card: #ffffff; --ink: #17181c; --muted: #6b6e76; --line: #e3e1da;
  --accent: #b3261e; --chip: #ebe9e2; --chip-on: #17181c; --chip-on-ink: #fff; --def: #fbf4e2;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101114; --card: #1a1c21; --ink: #ececea; --muted: #9a9ca3; --line: #2a2d33;
    --accent: #ff6b5e; --chip: #24262c; --chip-on: #ececea; --chip-on-ink: #101114; --def: #2a2618;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--ink); font: 16px/1.5 -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
  -webkit-text-size-adjust: 100%; padding-bottom: env(safe-area-inset-bottom); }
a { color: inherit; }
header { position: sticky; top: 0; z-index: 10; background: var(--bg); padding: calc(env(safe-area-inset-top) + 12px) 16px 0;
  border-bottom: 1px solid var(--line); }
.top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
h1 { font-size: 22px; letter-spacing: -0.02em; }
h1 span { color: var(--accent); }
.maj { font-size: 12px; color: var(--muted); }
.tabs { display: flex; gap: 20px; margin-top: 10px; }
.tab { background: none; border: 0; color: var(--muted); font: inherit; font-weight: 600; font-size: 15px;
  padding: 8px 0 10px; border-bottom: 2px solid transparent; cursor: pointer; }
.tab[aria-selected="true"] { color: var(--ink); border-color: var(--accent); }
main { max-width: 680px; margin: 0 auto; padding: 16px; }
.vue { display: none; } .vue.on { display: block; }
.intro { font-size: 17px; line-height: 1.55; margin-bottom: 18px; }
.sujet { background: var(--card); border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid var(--line); }
.kicker { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); }
.sujet h2 { font-size: 18px; line-height: 1.3; margin: 4px 0 8px; letter-spacing: -0.01em; }
.sujet p { font-size: 15px; }
.enjeux { margin-top: 8px; padding-left: 10px; border-left: 3px solid var(--accent); color: var(--muted); font-size: 14px; }
.sources-sujet { margin-top: 10px; }
.sources-sujet summary { font-size: 13px; color: var(--muted); cursor: pointer; padding: 4px 0; }
.sources-sujet li { list-style: none; font-size: 14px; padding: 6px 0; border-top: 1px solid var(--line); }
.sources-sujet li a { text-decoration: none; }
.sources-sujet b { font-weight: 600; color: var(--muted); font-size: 12px; margin-right: 4px; }
.signaux { background: var(--card); border: 1px dashed var(--line); border-radius: 14px; padding: 16px; }
.signaux h3 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.signaux li { margin: 6px 0 0 18px; font-size: 15px; }
.vide { color: var(--muted); text-align: center; padding: 32px 0; }
.filtres { display: flex; gap: 6px; overflow-x: auto; padding: 0 0 12px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.filtres::-webkit-scrollbar { display: none; }
.chip { flex: none; border: 0; background: var(--chip); color: var(--ink); border-radius: 999px; padding: 7px 13px;
  font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; }
.chip[aria-pressed="true"] { background: var(--chip-on); color: var(--chip-on-ink); }
.recherche { width: 100%; font: inherit; font-size: 16px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--line);
  background: var(--card); color: var(--ink); margin-bottom: 10px; }
.art { padding: 14px 0; border-bottom: 1px solid var(--line); }
.art .meta { font-size: 12px; color: var(--muted); display: flex; gap: 6px; flex-wrap: wrap; }
.art .meta .src { font-weight: 700; color: var(--ink); }
.art .meta .analyse { color: var(--accent); font-weight: 600; }
.art h3 { font-size: 16px; line-height: 1.35; margin: 3px 0 4px; }
.art h3 a { text-decoration: none; }
.art p { font-size: 14px; color: var(--muted); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.art.ouvert p { -webkit-line-clamp: unset; }
.def { margin-top: 6px; background: var(--def); border-radius: 8px; padding: 6px 10px; font-size: 13px; }
.compteur { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
</style>
</head>
<body>
<header>
  <div class="top">
    <h1>Veille<span>.</span></h1>
    <div class="maj">MAJ {{ maj }}</div>
  </div>
  <nav class="tabs" role="tablist">
    <button class="tab" role="tab" data-vue="brief" aria-selected="true">Brief</button>
    <button class="tab" role="tab" data-vue="fil" aria-selected="false">Fil ({{ articles|length }})</button>
  </nav>
</header>

<main>
<section id="brief" class="vue on">
{% if brief %}
  <p class="intro">{{ brief.vue_ensemble }}</p>
  {% for s in brief.sujets %}
  <article class="sujet">
    <div class="kicker">{{ s.region }}</div>
    <h2>{{ s.titre }}</h2>
    <p>{{ s.synthese }}</p>
    <p class="enjeux">{{ s.enjeux }}</p>
    {% if s.article_ids %}
    <details class="sources-sujet">
      <summary>{{ s.article_ids|length }} source{{ 's' if s.article_ids|length > 1 }}</summary>
      <ul>
      {% for id in s.article_ids %}{% set a = par_id[id] %}
        <li><b>{{ a.source }}</b><a href="{{ a.lien|lien_sur }}" target="_blank" rel="noopener">{{ a.titre }}</a></li>
      {% endfor %}
      </ul>
    </details>
    {% endif %}
  </article>
  {% endfor %}
  {% if brief.signaux_faibles %}
  <div class="signaux">
    <h3>Signaux faibles</h3>
    <ul>{% for sig in brief.signaux_faibles %}<li>{{ sig }}</li>{% endfor %}</ul>
  </div>
  {% endif %}
{% else %}
  <p class="vide">Pas de brief IA pour cette édition.<br>Consultez le fil.</p>
{% endif %}
</section>

<section id="fil" class="vue">
  <input class="recherche" type="search" placeholder="Rechercher (pays, acteur…)" aria-label="Rechercher">
  <div class="filtres" data-groupe="region">
    <button class="chip" data-val="" aria-pressed="true">Tout</button>
    {% for r in regions %}<button class="chip" data-val="{{ r }}" aria-pressed="false">{{ r }}</button>{% endfor %}
  </div>
  <div class="filtres" data-groupe="type">
    <button class="chip" data-val="" aria-pressed="true">Toutes sources</button>
    <button class="chip" data-val="presse" aria-pressed="false">Presse</button>
    <button class="chip" data-val="analyse" aria-pressed="false">Analyses</button>
  </div>
  <div class="compteur"></div>
  {% for a in articles %}
  <div class="art" data-regions="{{ a.regions|join('|') }}" data-type="{{ a.type_source }}" data-ts="{{ a.timestamp }}">
    <div class="meta"><span class="src">{{ a.source }}</span>{% if a.type_source == 'analyse' %}<span class="analyse">Analyse</span>{% endif %}<span class="quand"></span></div>
    <h3><a href="{{ a.lien|lien_sur }}" target="_blank" rel="noopener">{{ a.titre }}</a></h3>
    {% if a.resume %}<p>{{ a.resume }}</p>{% endif %}
    {% for terme, d in a.termes_definis.items() %}<div class="def"><b>{{ terme }}</b> — {{ d }}</div>{% endfor %}
  </div>
  {% endfor %}
</section>
</main>

<script>
(() => {
  const tabs = document.querySelectorAll('.tab');
  const montrer = (v) => {
    tabs.forEach(t => t.setAttribute('aria-selected', t.dataset.vue === v));
    document.querySelectorAll('.vue').forEach(s => s.classList.toggle('on', s.id === v));
    try { localStorage.setItem('veille-vue', v); } catch (e) {}
    window.scrollTo(0, 0);
  };
  tabs.forEach(t => t.addEventListener('click', () => montrer(t.dataset.vue)));
  try { const v = localStorage.getItem('veille-vue'); if (v) montrer(v); } catch (e) {}

  const now = Date.now() / 1000;
  document.querySelectorAll('.art').forEach(el => {
    const d = Math.max(0, now - +el.dataset.ts);
    el.querySelector('.quand').textContent = d < 3600 ? `il y a ${Math.max(1, Math.round(d / 60))} min`
      : d < 86400 ? `il y a ${Math.round(d / 3600)} h` : `il y a ${Math.round(d / 86400)} j`;
    el.querySelector('p')?.addEventListener('click', () => el.classList.toggle('ouvert'));
  });

  const etat = { region: '', type: '', q: '' };
  const arts = [...document.querySelectorAll('.art')];
  const compteur = document.querySelector('.compteur');
  const norm = s => s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  arts.forEach(a => a._txt = norm(a.textContent));
  const filtrer = () => {
    const q = norm(etat.q.trim());
    let n = 0;
    arts.forEach(a => {
      const ok = (!etat.region || a.dataset.regions.split('|').includes(etat.region))
        && (!etat.type || a.dataset.type === etat.type)
        && (!q || a._txt.includes(q));
      a.style.display = ok ? '' : 'none';
      if (ok) n++;
    });
    compteur.textContent = `${n} article${n > 1 ? 's' : ''}`;
  };
  document.querySelectorAll('.filtres').forEach(g => g.addEventListener('click', e => {
    const b = e.target.closest('.chip'); if (!b) return;
    g.querySelectorAll('.chip').forEach(c => c.setAttribute('aria-pressed', c === b));
    etat[g.dataset.groupe] = b.dataset.val; filtrer();
  }));
  document.querySelector('.recherche').addEventListener('input', e => { etat.q = e.target.value; filtrer(); });
  filtrer();
})();
</script>
</body>
</html>
"""

ICONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#14161c"/>
<circle cx="256" cy="256" r="150" fill="none" stroke="#ececea" stroke-width="28"/>
<path d="M106 256h300M256 106c-60 70-60 230 0 300M256 106c60 70 60 230 0 300" fill="none" stroke="#ececea" stroke-width="20"/>
<circle cx="380" cy="380" r="44" fill="#ff6b5e"/>
</svg>
"""

MANIFEST = {
    "name": "Veille géopolitique",
    "short_name": "Veille",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#14161c",
    "theme_color": "#14161c",
    "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"}],
}


def _lien_sur(url: str) -> str:
    return url if url.startswith(("https://", "http://")) else "#"


def construire_site(articles: list[Article], brief: Brief | None, dossier: Path) -> Path:
    env = Environment(autoescape=True)
    env.filters["lien_sur"] = _lien_sur
    html = env.from_string(TEMPLATE).render(
        articles=articles,
        brief=brief,
        par_id={a.id: a for a in articles},
        regions=list(REGIONS),
        maj=datetime.now(PARIS).strftime("%d/%m %H:%M"),
    )
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "index.html").write_text(html, encoding="utf-8")
    (dossier / "icon.svg").write_text(ICONE, encoding="utf-8")
    (dossier / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")
    return dossier / "index.html"
