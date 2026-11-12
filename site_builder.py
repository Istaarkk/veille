import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment

from config import REGIONS
from scraper import Article

PARIS = ZoneInfo("Europe/Paris")

TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f6f4ee" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1013" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Veille">
<meta name="robots" content="noindex">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon.svg">
<title>Veille</title>
<style>
:root {
  --bg: #f6f4ee; --card: #fffefb; --ink: #15161a; --soft: #3d3f46; --muted: #73757d; --line: #e2dfd5;
  --accent: #c2271d; --accent-bg: #fbe9e6; --chip: #eae7dd; --ok: #2e8b57; --warn: #b7791f; --def: #f7efd9;
  --serif: ui-serif, "New York", "Iowan Old Style", Georgia, "Noto Serif", serif;
  --sans: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1013; --card: #17191d; --ink: #edece8; --soft: #c6c6c2; --muted: #8e9098; --line: #272a30;
    --accent: #ff6f61; --accent-bg: #2b1715; --chip: #22252b; --ok: #4cc38a; --warn: #e0a84a; --def: #27220f;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-padding-top: 110px; }
body { background: var(--bg); color: var(--ink); font: 16px/1.5 var(--sans); -webkit-text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent; padding-bottom: calc(env(safe-area-inset-bottom) + 32px); }
a { color: inherit; }
button { font: inherit; color: inherit; cursor: pointer; }

header { position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--bg) 88%, transparent);
  -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); border-bottom: 1px solid var(--line);
  padding: calc(env(safe-area-inset-top) + 10px) 16px 0; }
.barre { max-width: 680px; margin: 0 auto; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
h1 { font: 700 24px/1 var(--serif); letter-spacing: -0.02em; }
h1 span { color: var(--accent); }
.frais { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.frais::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }
.frais.vieux::before { background: var(--warn); }
.tabs { display: flex; gap: 22px; margin-top: 8px; }
.tab { background: none; border: 0; color: var(--muted); font-weight: 600; font-size: 15px; padding: 8px 0 10px;
  border-bottom: 2px solid transparent; margin-bottom: -1px; display: flex; align-items: center; gap: 6px; }
.tab[aria-selected="true"] { color: var(--ink); border-color: var(--accent); }
.pastille { background: var(--accent); color: #fff; font-size: 11px; font-weight: 700; border-radius: 999px; padding: 1px 7px; line-height: 1.5; }
.pastille:empty { display: none; }

main { max-width: 680px; margin: 0 auto; padding: 14px 16px 0; }
.vue { display: none; } .vue.on { display: block; }
.vide { color: var(--muted); text-align: center; padding: 40px 0; }

/* ---------- Brief ---------- */
.edition { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 12px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
.edition .vieux { color: var(--warn); }
.lien-btn { background: none; border: 0; color: var(--muted); font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; padding: 8px 0 8px 12px; }
.accroche { font: 500 19px/1.4 var(--serif); letter-spacing: -0.005em; margin: 6px 0 14px; text-wrap: pretty; }

.sujets { background: var(--card); border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
.sujet + .sujet { border-top: 1px solid var(--line); }
.sujet summary { list-style: none; display: grid; grid-template-columns: 26px 1fr 14px; column-gap: 8px; padding: 14px 14px 14px 12px; cursor: pointer; }
.sujet summary::-webkit-details-marker { display: none; }
.rang { font: 700 20px/1.2 var(--serif); color: var(--muted); font-variant-numeric: tabular-nums; text-align: center; padding-top: 14px; }
.sujet:nth-child(-n+3) .rang { color: var(--accent); }
.kicker { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted);
  display: flex; align-items: center; gap: 6px; }
.neuf { display: none; background: var(--accent-bg); color: var(--accent); border-radius: 4px; padding: 0 5px; letter-spacing: 0.04em; }
.sujet.neuf-oui .neuf { display: inline; }
.sujet h2 { font: 700 18px/1.25 var(--serif); letter-spacing: -0.01em; margin: 2px 0 3px; text-wrap: balance; }
.bref { font-size: 15px; line-height: 1.45; color: var(--soft); text-wrap: pretty; }
.chevron { align-self: center; width: 9px; height: 9px; border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted);
  transform: rotate(45deg); transition: transform .15s; opacity: .7; }
.sujet[open] .chevron { transform: rotate(-135deg); }
.detail { padding: 0 14px 16px 46px; }
.points li { list-style: none; position: relative; font-size: 15px; line-height: 1.45; padding: 4px 0 4px 14px; }
.points li::before { content: ""; position: absolute; left: 0; top: 13px; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }
.surveiller { margin-top: 10px; background: var(--accent-bg); border-radius: 10px; padding: 9px 12px; font-size: 14px; line-height: 1.45; }
.surveiller b { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em; color: var(--accent); }
.sources { margin-top: 10px; }
.sources a { display: block; text-decoration: none; font-size: 14px; line-height: 1.35; padding: 9px 0; border-top: 1px solid var(--line); }
.sources a b { display: block; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

.signaux { margin-top: 18px; }
.titre-bloc { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); margin-bottom: 4px; }
.signaux li { list-style: none; font-size: 15px; line-height: 1.45; padding: 9px 0 9px 14px; border-top: 1px solid var(--line); position: relative; }
.signaux li::before { content: ""; position: absolute; left: 0; top: 18px; width: 6px; height: 2px; background: var(--muted); }

/* ---------- Fil ---------- */
.recherche { width: 100%; font: inherit; font-size: 16px; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--line);
  background: var(--card); color: var(--ink); margin-bottom: 10px; -webkit-appearance: none; appearance: none; }
.filtres { display: flex; gap: 6px; overflow-x: auto; margin: 0 -16px; padding: 0 16px 8px; scrollbar-width: none; }
.filtres::-webkit-scrollbar { display: none; }
.chip { flex: none; border: 0; background: var(--chip); border-radius: 999px; padding: 8px 14px; font-size: 13px; font-weight: 500; }
.chip[aria-pressed="true"] { background: var(--ink); color: var(--bg); }
.compteur { font-size: 12px; color: var(--muted); padding: 2px 0 6px; font-variant-numeric: tabular-nums; }
.art { padding: 11px 0 11px 12px; border-top: 1px solid var(--line); position: relative; cursor: pointer; }
.art.neuf-oui::before { content: ""; position: absolute; left: 0; top: 17px; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
.art .meta { font-size: 12px; color: var(--muted); display: flex; gap: 6px; flex-wrap: wrap; font-variant-numeric: tabular-nums; }
.art .src { font-weight: 700; color: var(--soft); }
.art .analyse { color: var(--accent); font-weight: 600; }
.art h3 { font-size: 16px; font-weight: 600; line-height: 1.3; margin: 2px 0 0; text-wrap: pretty; }
.art h3 a { text-decoration: none; }
.art p { font-size: 14px; line-height: 1.45; color: var(--muted); margin-top: 3px; display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; }
.art.ouvert p { -webkit-line-clamp: unset; color: var(--soft); }
.compact .art:not(.ouvert) p { display: none; }
.def { display: none; margin-top: 6px; background: var(--def); border-radius: 8px; padding: 6px 10px; font-size: 13px; }
.art.ouvert .def { display: block; }
.deja { display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); padding: 10px 0; border-top: 1px solid var(--line); }
.deja::after { content: ""; flex: 1; height: 1px; background: var(--line); }
</style>
</head>
<body data-genere="{{ genere }}">
<header>
  <div class="barre">
    <div class="top">
      <h1>Veille<span>.</span></h1>
      <div class="frais" title="Dernière mise à jour du fil"></div>
    </div>
    <nav class="tabs" role="tablist">
      <button class="tab" role="tab" data-vue="brief" aria-selected="true">Brief</button>
      <button class="tab" role="tab" data-vue="fil" aria-selected="false">Fil <span class="pastille"></span></button>
    </nav>
  </div>
</header>

<main>
<section id="brief" class="vue on">
{% if brief %}
  <div class="edition">
    <span>{{ date_longue }} · <span class="age-brief" data-ts="{{ brief.genere }}">brief de {{ heure_brief }}</span></span>
    <button class="lien-btn" id="deplier">Tout déplier</button>
  </div>
  <p class="accroche">{{ brief.accroche }}</p>
  <div class="sujets">
  {% for s in brief.sujets %}
  <details class="sujet" data-ts="{{ s.ts }}">
    <summary>
      <span class="rang">{{ loop.index }}</span>
      <span>
        <span class="kicker">{{ s.region }}<span class="neuf">Nouveau</span></span>
        <h2>{{ s.titre }}</h2>
        <p class="bref">{{ s.en_bref }}</p>
      </span>
      <span class="chevron" aria-hidden="true"></span>
    </summary>
    <div class="detail">
      <ul class="points">{% for p in s.points %}<li>{{ p }}</li>{% endfor %}</ul>
      {% if s.a_surveiller %}<p class="surveiller"><b>À surveiller</b>{{ s.a_surveiller }}</p>{% endif %}
      {% if s.sources %}
      <div class="sources">
        {% for a in s.sources %}<a href="{{ a.lien|lien_sur }}" target="_blank" rel="noopener"><b>{{ a.source }}</b>{{ a.titre }}</a>{% endfor %}
      </div>
      {% endif %}
    </div>
  </details>
  {% endfor %}
  </div>
  {% if brief.signaux_faibles %}
  <div class="signaux">
    <div class="titre-bloc">Signaux faibles</div>
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
    <button class="chip" id="compact" aria-pressed="false">Titres seuls</button>
  </div>
  <div class="compteur"></div>
  <div class="liste">
  {% for a in articles %}
  <div class="art" data-regions="{{ a.regions|join('|') }}" data-type="{{ a.type_source }}" data-ts="{{ a.timestamp }}">
    <div class="meta"><span class="src">{{ a.source }}</span>{% if a.type_source == 'analyse' %}<span class="analyse">Analyse</span>{% endif %}<span class="quand"></span></div>
    <h3><a href="{{ a.lien|lien_sur }}" target="_blank" rel="noopener">{{ a.titre }}</a></h3>
    {% if a.resume %}<p>{{ a.resume }}</p>{% endif %}
    {% for terme, d in a.termes_definis.items() %}<div class="def"><b>{{ terme }}</b> — {{ d }}</div>{% endfor %}
  </div>
  {% endfor %}
  </div>
</section>
</main>

<script>
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const lire = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const ecrire = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const now = Date.now() / 1000;
  const age = ts => { const d = Math.max(0, now - ts);
    return d < 3600 ? `${Math.max(1, Math.round(d / 60))} min` : d < 86400 ? `${Math.round(d / 3600)} h` : `${Math.round(d / 86400)} j`; };

  // Onglets
  const tabs = $$('.tab');
  const montrer = (v, haut) => {
    tabs.forEach(t => t.setAttribute('aria-selected', t.dataset.vue === v));
    $$('.vue').forEach(s => s.classList.toggle('on', s.id === v));
    ecrire('veille-vue', v);
    if (haut) window.scrollTo(0, 0);
  };
  tabs.forEach(t => t.addEventListener('click', () => montrer(t.dataset.vue, true)));
  if (lire('veille-vue') === 'fil' || !$('.sujet')) montrer('fil');

  // Fraîcheur : l'âge des données est toujours visible, et une page restée ouverte se recharge au retour.
  const genere = +document.body.dataset.genere;
  const frais = $('.frais');
  frais.textContent = `il y a ${age(genere)}`;
  frais.classList.toggle('vieux', now - genere > 3 * 3600);
  const ageBrief = $('.age-brief');
  if (ageBrief && now - +ageBrief.dataset.ts > 8 * 3600) ageBrief.classList.add('vieux');
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) ecrire('veille-vu', Math.floor(Date.now() / 1000));
    else if (Date.now() / 1000 - now > 20 * 60) location.reload();
  });
  addEventListener('pagehide', () => ecrire('veille-vu', Math.floor(Date.now() / 1000)));

  // Nouveautés depuis la dernière visite
  const vu = +lire('veille-vu') || 0;
  const arts = $$('.art');
  let neufs = 0;
  arts.forEach(el => {
    const ts = +el.dataset.ts;
    $('.quand', el).textContent = age(ts);
    if (vu && ts > vu) { el.classList.add('neuf-oui'); neufs++; }
    el.addEventListener('click', e => { if (!e.target.closest('a')) el.classList.toggle('ouvert'); });
  });
  if (neufs) $('.pastille').textContent = neufs;
  $$('.sujet').forEach(s => { if (vu && +s.dataset.ts > vu) s.classList.add('neuf-oui'); });
  let deja = null;
  if (neufs && neufs < arts.length) {
    deja = document.createElement('div');
    deja.className = 'deja'; deja.textContent = 'Déjà vu';
    arts.find(a => !a.classList.contains('neuf-oui')).before(deja);
  }

  // Brief : tout déplier / replier
  const deplier = $('#deplier');
  deplier?.addEventListener('click', () => {
    const ouvrir = $$('.sujet').some(s => !s.open);
    $$('.sujet').forEach(s => s.open = ouvrir);
    deplier.textContent = ouvrir ? 'Tout replier' : 'Tout déplier';
  });

  // Fil : filtres, recherche, mode compact
  const etat = { region: '', type: '', q: '' };
  const compteur = $('.compteur');
  const norm = s => s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  arts.forEach(a => a._txt = norm(a.textContent));
  const filtrer = () => {
    const q = norm(etat.q.trim());
    let n = 0, nn = 0;
    arts.forEach(a => {
      const ok = (!etat.region || a.dataset.regions.split('|').includes(etat.region))
        && (!etat.type || a.dataset.type === etat.type)
        && (!q || a._txt.includes(q));
      a.style.display = ok ? '' : 'none';
      if (ok) { n++; if (a.classList.contains('neuf-oui')) nn++; }
    });
    compteur.textContent = `${n} article${n > 1 ? 's' : ''}` + (nn ? ` · ${nn} nouveau${nn > 1 ? 'x' : ''}` : '');
    if (deja) deja.style.display = nn && nn < n ? '' : 'none';
  };
  const compact = $('#compact'), fil = $('#fil');
  const regler = on => { fil.classList.toggle('compact', on); compact.setAttribute('aria-pressed', on); };
  regler(lire('veille-compact') === '1');
  $$('.filtres').forEach(g => g.addEventListener('click', e => {
    const b = e.target.closest('.chip'); if (!b) return;
    if (b === compact) { const on = !fil.classList.contains('compact'); regler(on); ecrire('veille-compact', on ? '1' : '0'); return; }
    $$('.chip', g).forEach(c => c !== compact && c.setAttribute('aria-pressed', c === b));
    etat[g.dataset.groupe] = b.dataset.val; filtrer();
  }));
  $('.recherche').addEventListener('input', e => { etat.q = e.target.value; filtrer(); });
  filtrer();
})();
</script>
</body>
</html>
"""

ICONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#0f1013"/>
<circle cx="256" cy="256" r="150" fill="none" stroke="#ececea" stroke-width="28"/>
<path d="M106 256h300M256 106c-60 70-60 230 0 300M256 106c60 70 60 230 0 300" fill="none" stroke="#ececea" stroke-width="20"/>
<circle cx="380" cy="380" r="44" fill="#ff6f61"/>
</svg>
"""

MANIFEST = {
    "name": "Veille géopolitique",
    "short_name": "Veille",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#0f1013",
    "theme_color": "#0f1013",
    "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"}],
}


def _lien_sur(url: str) -> str:
    return url if url.startswith(("https://", "http://")) else "#"


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def construire_site(articles: list[Article], brief: dict | None, dossier: Path) -> Path:
    env = Environment(autoescape=True)
    env.filters["lien_sur"] = _lien_sur
    maintenant = datetime.now(PARIS)
    html = env.from_string(TEMPLATE).render(
        articles=articles,
        brief=brief,
        regions=list(REGIONS),
        genere=int(maintenant.timestamp()),
        date_longue=f"{JOURS[maintenant.weekday()]} {maintenant.day} {MOIS[maintenant.month - 1]}",
        heure_brief=datetime.fromtimestamp(brief["genere"], PARIS).strftime("%H:%M") if brief else "",
    )
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "index.html").write_text(html, encoding="utf-8")
    (dossier / "icon.svg").write_text(ICONE, encoding="utf-8")
    (dossier / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")
    return dossier / "index.html"
