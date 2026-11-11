"use strict";

// ================================================================ Zustand

let KURS = null;
const raumCache = {};

const speicher = {
  lesen(schluessel, vorgabe) {
    try {
      const roh = localStorage.getItem("spotkurs:" + schluessel);
      return roh === null ? vorgabe : JSON.parse(roh);
    } catch (e) { return vorgabe; }
  },
  schreiben(schluessel, wert) {
    try { localStorage.setItem("spotkurs:" + schluessel, JSON.stringify(wert)); } catch (e) { /* egal */ }
  },
  loeschen(schluessel) {
    try { localStorage.removeItem("spotkurs:" + schluessel); } catch (e) { /* egal */ }
  },
};

// Punkte: { "<kapitel>/<abschnitt>/<block>": erreichte Punkte }
function punkteLesen() { return speicher.lesen("punkte", {}); }
function punkteSetzen(schluessel, wert) {
  const p = punkteLesen();
  p[schluessel] = Math.max(p[schluessel] || 0, wert);
  speicher.schreiben("punkte", p);
  punktestandZeigen();
}
// Quiz-Verlauf: { schluessel: { falsch: [indices], geloest: bool } }
function quizLesen(s) { return speicher.lesen("quiz:" + s, { falsch: [], geloest: false }); }
function quizSchreiben(s, v) { speicher.schreiben("quiz:" + s, v); }

function moeglichePunkte(abschnitt) {
  return abschnitt.bloecke.reduce((s, b) => s + (b.punkte || 0), 0);
}
function erreichtePunkte(kid, ai, abschnitt) {
  const p = punkteLesen();
  return abschnitt.bloecke.reduce((s, b, bi) => s + (p[`${kid}/${ai}/${bi}`] || 0), 0);
}

function punktestandZeigen() {
  if (!KURS) return;
  let ist = 0, soll = 0;
  for (const k of KURS.kapitel) {
    k.abschnitte.forEach((a, ai) => { soll += moeglichePunkte(a); ist += erreichtePunkte(k.id, ai, a); });
  }
  document.getElementById("punktestand").innerHTML = soll ? `Punkte <b>${ist}</b> / ${soll}` : "";
}

// ================================================================ Hilfen

function el(tag, attrs = {}, ...kinder) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v !== null && v !== undefined) e.setAttribute(k, v);
  }
  for (const kind of kinder.flat()) {
    if (kind === null || kind === undefined || kind === false) continue;
    e.append(kind instanceof Node ? kind : document.createTextNode(String(kind)));
  }
  return e;
}

function esc(t) {
  return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Kleiner Markdown-Leser: Absätze, ## Titel, Listen, > Hinweise, **fett**, *kursiv*, `code`, [Links](url)
function inline(t) {
  return esc(t)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

function markdown(text) {
  const zeilen = text.split("\n");
  let html = "", absatz = [], liste = null, hinweis = [], code = [];
  const codeEnde = () => {
    if (code.length) { html += `<div class="codefeld"><div class="editor nurlesen"><div class="nummern">${code.map((_, i) => i + 1).join("\n")}</div><div class="flaeche"><pre>${einfaerben(code.join("\n"))}</pre></div></div></div>`; code = []; }
  };
  const absatzEnde = () => { codeEnde(); if (absatz.length) { html += `<p>${inline(absatz.join(" "))}</p>`; absatz = []; } };
  const listeEnde = () => { if (liste) { html += `</${liste}>`; liste = null; } };
  const hinweisEnde = () => {
    if (hinweis.length) { html += `<div class="hinweisbox">${markdown(hinweis.join("\n"))}</div>`; hinweis = []; }
  };
  for (const z of zeilen) {
    const cz = z.match(/^\|\s?(.*)$/);
    if (cz) { if (absatz.length) { const a = absatz; absatz = []; html += `<p>${inline(a.join(" "))}</p>`; } listeEnde(); code.push(cz[1]); continue; }
    codeEnde();
    if (z.startsWith(">")) { absatzEnde(); listeEnde(); hinweis.push(z.replace(/^>\s?/, "")); continue; }
    hinweisEnde();
    const ul = z.match(/^\s*[-•]\s+(.*)$/);
    const ol = z.match(/^\s*\d+[.)]\s+(.*)$/);
    if (z.startsWith("## ")) { absatzEnde(); listeEnde(); html += `<h2>${inline(z.slice(3))}</h2>`; }
    else if (ul || ol) {
      absatzEnde();
      const art = ul ? "ul" : "ol";
      if (liste !== art) { listeEnde(); html += `<${art}>`; liste = art; }
      html += `<li>${inline((ul || ol)[1])}</li>`;
    }
    else if (!z.trim()) { absatzEnde(); listeEnde(); }
    else if (liste && /^\s{2,}/.test(z)) { html = html.replace(/<\/li>$/, " " + inline(z.trim()) + "</li>"); }
    else { listeEnde(); absatz.push(z.trim()); }
  }
  absatzEnde(); listeEnde(); hinweisEnde();
  return html;
}

// ================================================================ Python einfärben

const SCHLUESSELWOERTER = new Set(("False None True and as assert break class continue def del elif else except " +
  "finally for from global if import in is lambda nonlocal not or pass raise return try while with yield").split(" "));
const EINGEBAUT = new Set("print range len abs round int float str min max sum list type input enumerate".split(" "));

function einfaerben(code) {
  const muster = /(#[^\n]*)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g;
  let aus = "", letzte = 0, m;
  while ((m = muster.exec(code))) {
    aus += esc(code.slice(letzte, m.index));
    const [ganz, kom, str, zahl, wort] = m;
    if (kom) aus += `<span class="tok-com">${esc(kom)}</span>`;
    else if (str) aus += `<span class="tok-str">${esc(str)}</span>`;
    else if (zahl) aus += `<span class="tok-num">${zahl}</span>`;
    else if (SCHLUESSELWOERTER.has(wort)) aus += `<span class="tok-kw">${wort}</span>`;
    else if (wort === "spot") aus += `<span class="tok-spot">${wort}</span>`;
    else if (EINGEBAUT.has(wort) || code[m.index + wort.length] === "(") aus += `<span class="tok-fn">${wort}</span>`;
    else aus += esc(wort);
    letzte = m.index + ganz.length;
  }
  return aus + esc(code.slice(letzte)) + "\n";
}

function editorBauen(code, { nurLesen = false, beiAenderung = null } = {}) {
  const nummern = el("div", { class: "nummern" });
  const pre = el("pre");
  const ta = el("textarea", { spellcheck: "false", autocapitalize: "off", autocomplete: "off" });
  ta.value = code;
  const huelle = el("div", { class: "editor" + (nurLesen ? " nurlesen" : "") },
    nummern, el("div", { class: "flaeche" }, pre, ta));
  function zeichnen() {
    pre.innerHTML = einfaerben(ta.value);
    const n = ta.value.split("\n").length;
    nummern.textContent = Array.from({ length: n }, (_, i) => i + 1).join("\n");
    ta.style.height = pre.offsetHeight ? pre.offsetHeight + "px" : "";
  }
  ta.addEventListener("input", () => { zeichnen(); beiAenderung && beiAenderung(ta.value); });
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const a = ta.selectionStart, b = ta.selectionEnd;
      ta.value = ta.value.slice(0, a) + "    " + ta.value.slice(b);
      ta.selectionStart = ta.selectionEnd = a + 4;
      ta.dispatchEvent(new Event("input"));
    } else if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
      // Einrückung der Zeile übernehmen, nach ":" eine Stufe mehr
      e.preventDefault();
      const a = ta.selectionStart;
      const zeilenAnfang = ta.value.lastIndexOf("\n", a - 1) + 1;
      const zeile = ta.value.slice(zeilenAnfang, a);
      let einzug = zeile.match(/^\s*/)[0];
      if (/:\s*$/.test(zeile)) einzug += "    ";
      ta.value = ta.value.slice(0, a) + "\n" + einzug + ta.value.slice(ta.selectionEnd);
      ta.selectionStart = ta.selectionEnd = a + 1 + einzug.length;
      ta.dispatchEvent(new Event("input"));
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
    }
  });
  zeichnen();
  requestAnimationFrame(zeichnen);
  return { huelle, wert: () => ta.value, setzen: (t) => { ta.value = t; zeichnen(); }, textfeld: ta };
}

// ================================================================ Karte (Raum + Spots Weg)

async function raumHolen(name) {
  if (!raumCache[name]) {
    const antwort = await fetch(`raeume/${encodeURIComponent(name)}.json`);
    raumCache[name] = antwort.ok ? await antwort.json() : null;
  }
  return raumCache[name];
}

const SVGNS = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

function karteBauen(raum, startposen) {
  const box = el("div", { class: "karte" });
  let minx = 0, miny = 0, maxx = 4, maxy = 4;
  if (raum.groesse) { maxx = raum.groesse[0]; maxy = raum.groesse[1]; }
  else {
    const xs = [], ys = [];
    raum.waende.forEach((w) => { xs.push(w[0], w[2]); ys.push(w[1], w[3]); });
    if (xs.length) { minx = Math.min(...xs); maxx = Math.max(...xs); miny = Math.min(...ys); maxy = Math.max(...ys); }
  }
  const rand = 0.35;
  const breite = maxx - minx + 2 * rand, hoehe = maxy - miny + 2 * rand;
  // y zeigt nach oben: wir spiegeln mit einer Gruppe
  const svg = s("svg", { viewBox: `${minx - rand} ${-(maxy + rand)} ${breite} ${hoehe}`, preserveAspectRatio: "xMidYMid meet" });
  svg.style.aspectRatio = `${breite} / ${hoehe}`;
  const welt = s("g", { transform: "scale(1,-1)" });
  svg.append(welt);

  // Gitter alle 1 m
  for (let x = Math.ceil(minx); x <= maxx; x++) welt.append(s("line", { x1: x, y1: miny, x2: x, y2: maxy, stroke: "#e2e4e5", "stroke-width": 0.012 }));
  for (let y = Math.ceil(miny); y <= maxy; y++) welt.append(s("line", { x1: minx, y1: y, x2: maxx, y2: y, stroke: "#e2e4e5", "stroke-width": 0.012 }));
  // Achsenbeschriftung
  for (let x = Math.ceil(minx); x <= maxx; x++) {
    const t = s("text", { x, y: -(miny - 0.22), "font-size": 0.14, fill: "#a0a4a8", "text-anchor": "middle", transform: "scale(1,-1)" });
    t.textContent = x; welt.append(t);
  }
  for (let y = Math.ceil(miny); y <= maxy; y++) {
    const t = s("text", { x: minx - 0.18, y: -y + 0.05, "font-size": 0.14, fill: "#a0a4a8", "text-anchor": "middle", transform: "scale(1,-1)" });
    t.textContent = y; welt.append(t);
  }

  const vieleck = (ecken, attrs) => s("polygon", { points: ecken.map((e) => e.join(",")).join(" "), ...attrs });
  (raum.boeden || []).forEach((b) => welt.append(vieleck(b.ecken, { fill: "#dfeef0", stroke: "#9cc9cd", "stroke-width": 0.02 })));
  (raum.sperrzonen || []).forEach((z) => welt.append(vieleck(z.ecken, { fill: "rgba(214,69,61,0.12)", stroke: "#d6453d", "stroke-width": 0.02, "stroke-dasharray": "0.08 0.05" })));
  (raum.bloecke || []).forEach((b) => {
    welt.append(vieleck(b.ecken, { fill: "#c7cacc", stroke: "#8e9396", "stroke-width": 0.02 }));
    const cx = b.ecken.reduce((a, e) => a + e[0], 0) / 4, cy = b.ecken.reduce((a, e) => a + e[1], 0) / 4;
    const t = s("text", { x: cx, y: -cy + 0.05, "font-size": 0.13, fill: "#5b6064", "text-anchor": "middle", transform: "scale(1,-1)" });
    t.textContent = b.name; welt.append(t);
  });
  raum.waende.forEach((w) => welt.append(s("line", { x1: w[0], y1: w[1], x2: w[2], y2: w[3], stroke: "#3a3f43", "stroke-width": 0.08, "stroke-linecap": "square" })));
  (raum.tags || []).forEach((t) => {
    const g = s("g", { transform: `translate(${t.x},${t.y}) rotate(${t.grad})` });
    g.append(s("rect", { x: -0.04, y: -0.13, width: 0.08, height: 0.26, fill: "#24282b" }));
    welt.append(g);
    const txt = s("text", { x: t.x - Math.cos(t.grad * Math.PI / 180) * -0.2, y: -(t.y - Math.sin(t.grad * Math.PI / 180) * -0.2) + 0.05, "font-size": 0.14, "font-weight": 700, fill: "#24282b", "text-anchor": "middle", transform: "scale(1,-1)" });
    txt.textContent = "Tag " + t.id; welt.append(txt);
  });

  // Je Startplatz ein Spot mit eigener Spurfarbe
  const ebene = s("g");
  welt.append(ebene);

  // raum=mensch-*: ein Mensch mit Tag auf dem Rücken geht einen festen Weg
  let mensch = null;
  if (raum.mensch) {
    mensch = s("g");
    mensch.append(
      s("circle", { cx: 0, cy: 0, r: 0.2, fill: "#e8590c", stroke: "#24282b", "stroke-width": 0.03 }),
      s("circle", { cx: 0.07, cy: 0, r: 0.07, fill: "#f4d9c6" }),          // Kopf, schaut nach vorn
      s("rect", { x: -0.26, y: -0.09, width: 0.06, height: 0.18, fill: "#24282b" }),   // Tag auf dem Rücken
    );
    const name = s("text", { x: 0, y: 0.38, "font-size": 0.13, "font-weight": 700, fill: "#e8590c", "text-anchor": "middle", transform: "scale(1,-1)" });
    name.textContent = "Tag " + raum.mensch.tag;
    const huelle = s("g");
    huelle.append(mensch);
    const schild = s("g");
    schild.append(name);
    welt.append(huelle, schild);
    mensch.huelle = huelle; mensch.schild = schild;
  }
  function menschZeigen(p) {
    if (!mensch || !p) return;
    const [x, y, grad] = p;
    mensch.huelle.setAttribute("transform", `translate(${x},${y}) rotate(${grad})`);
    mensch.schild.setAttribute("transform", `translate(${x},${y - 0.55})`);
  }
  if (raum.mensch) menschZeigen(raum.mensch.lage);
  const legende = el("div", { class: "legende" });
  box.append(svg, legende);
  let roboter = [];

  function spotZeichnen(farbe, nummer) {
    const g = s("g");
    g.append(
      s("rect", { x: -0.55, y: -0.25, width: 1.1, height: 0.5, rx: 0.14, fill: "#f5c518", stroke: "#24282b", "stroke-width": 0.03 }),
      s("rect", { x: 0.3, y: -0.2, width: 0.2, height: 0.4, rx: 0.06, fill: "#24282b" }),
      s("circle", { cx: -0.1, cy: 0, r: 0.12, fill: farbe }),
    );
    if (nummer) {
      const t = s("text", { x: -0.1, y: 0.05, "font-size": 0.15, "font-weight": 700, fill: "white", "text-anchor": "middle", transform: "scale(1,-1)" });
      t.textContent = nummer; g.append(t);
    }
    return g;
  }

  function lage(r, x, y, grad) {
    r.spot.setAttribute("transform", `translate(${x},${y}) rotate(${grad})`);
    r.lage = [x, y, grad];
  }
  function legendeZeigen() {
    if (roboter.length === 1) {
      const [x, y, g] = roboter[0].lage;
      legende.textContent = `x = ${x.toFixed(2)} m   y = ${y.toFixed(2)} m   Blick = ${Math.round(((g % 360) + 540) % 360 - 180)}°`;
    } else {
      legende.textContent = `${roboter.length} Startplätze, dasselbe Programm`;
    }
  }
  function zuruecksetzen(posen) {
    ebene.innerHTML = "";
    roboter = posen.map((p, i) => {
      const farbe = SPURFARBEN[i % SPURFARBEN.length];
      const spur = s("polyline", { points: "", fill: "none", stroke: farbe, "stroke-width": 0.035, "stroke-linejoin": "round", "stroke-linecap": "round" });
      const stoesse = s("g");
      const spot = spotZeichnen(farbe, posen.length > 1 ? i + 1 : null);
      ebene.append(spur, stoesse);
      const r = { spur, stoesse, spot, lage: p, stossZahl: 0 };
      lage(r, p[0], p[1], p[2]);
      return r;
    });
    roboter.forEach((r) => ebene.append(r.spot));   // Roboter über allen Spuren
    if (raum.mensch) menschZeigen(raum.mensch.lage);
    legendeZeigen();
  }
  zuruecksetzen(startposen.length ? startposen : [raum.start]);

  return {
    box,
    zuruecksetzen,
    // spur: [[t, x, y, grad], ...] des Menschen; gezeigt wird der letzte Punkt bis t
    menschBei(spur, t) {
      if (!spur || !spur.length) return;
      let p = spur[0];
      for (const q of spur) { if (q[0] <= t) p = q; else break; }
      menschZeigen([p[1], p[2], p[3]]);
    },
    zeigen(i, weg, stoesse) {
      const r = roboter[i];
      if (!r) return;
      r.spur.setAttribute("points", weg.map(([, x, y]) => `${x},${y}`).join(" "));
      if (weg.length) { const [, x, y, g] = weg[weg.length - 1]; lage(r, x, y, g); }
      for (const [x, y] of stoesse.slice(r.stossZahl)) {
        if (x !== null && x !== undefined) r.stoesse.append(s("circle", { cx: x, cy: y, r: 0.09, fill: "none", stroke: "#d6453d", "stroke-width": 0.04 }));
      }
      r.stossZahl = stoesse.length;
      legendeZeigen();
    },
  };
}

const SPURFARBEN = ["#0ea5b0", "#e8590c", "#7048e8", "#2f9e44", "#c2255c", "#1971c2"];

// ================================================================ Trockenlauf: Spot als Zeichnung
//
// raum=trocken: spotlab baut die echten Befehle für Licht, Ton und Haltung, bewegt
// aber nichts. Die Bühne spielt sie ab: Spot von der Seite (pitch, Höhe), von vorne
// (roll) und von oben (yaw), LEDs in der befohlenen Farbe, Töne über den Lautsprecher.
// Vorzeichen wie bei spotlab: pitch positiv senkt die Nase, roll positiv hebt die
// linke Seite, yaw positiv dreht nach links.

const FARBNAMEN = { "0,0,255": "blau", "0,255,0": "grün", "255,0,0": "rot", "255,255,255": "weiss", "255,255,0": "gelb", "128,0,255": "violett" };
const NOTEN = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
const UEBERGANG_S = 0.6;   // nur für die Zeichnung: so lange dauert ein Haltungswechsel im Bild

function zustandBei(signale, t) {
  const z = { steh: 0, pose: { roll: 0, pitch: 0, yaw: 0, height: 0 }, licht: null, ton: null };
  let stehVon = 0, stehZiel = 0, stehT = -99;
  let poseVon = { ...z.pose }, poseZiel = { ...z.pose }, poseT = -99;
  const anteil = (t0, tt) => Math.max(0, Math.min(1, (tt - t0) / UEBERGANG_S));
  const stehBei = (tt) => stehVon + (stehZiel - stehVon) * anteil(stehT, tt);
  const poseBei = (tt) => {
    const a = anteil(poseT, tt), p = {};
    for (const k of Object.keys(poseZiel)) p[k] = poseVon[k] + (poseZiel[k] - poseVon[k]) * a;
    return p;
  };
  for (const s of signale) {
    if (s.t > t) break;
    if (s.art === "stand" || s.art === "sit" || s.art === "power_off") {
      stehVon = stehBei(s.t); stehZiel = s.art === "stand" ? 1 : 0; stehT = s.t;
      if (s.art !== "stand") { poseVon = poseBei(s.t); poseZiel = { roll: 0, pitch: 0, yaw: 0, height: 0 }; poseT = s.t; }
    } else if (s.art === "pose") {
      poseVon = poseBei(s.t);
      poseZiel = { roll: s.roll || 0, pitch: s.pitch || 0, yaw: s.yaw || 0, height: s.height || 0 };
      poseT = s.t;
    } else if (s.art === "lights" && t < s.t + s.duration) {
      z.licht = { rgb: s.color, hell: s.brightness };
    } else if (s.art === "beep" && t < s.t + s.duration) {
      z.ton = s;
    }
  }
  z.steh = stehBei(t);
  z.pose = poseBei(t);
  return z;
}

// Töne: ein Rechteckton wie ein Summer. Erst nach einem Klick erlaubt der Browser Ton.
const TON = {
  ctx: null,
  an() { return speicher.lesen("ton", true); },
  vorbereiten() {
    if (!this.an()) return;
    try {
      this.ctx = this.ctx || new (window.AudioContext || window.webkitAudioContext)();
      this.ctx.resume();
    } catch (e) { this.ctx = null; }
  },
  spielen(note, oktave, dauer) {
    if (!this.an() || !this.ctx) return;
    const midi = 12 * (oktave + 1) + (NOTEN[note] ?? 0);
    const osc = this.ctx.createOscillator(), laut = this.ctx.createGain();
    osc.type = "square";
    osc.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
    laut.gain.value = 0.05;
    osc.connect(laut).connect(this.ctx.destination);
    const jetzt = this.ctx.currentTime;
    osc.start(jetzt);
    osc.stop(jetzt + dauer);
  },
};

function buehneBauen() {
  const box = el("div", { class: "karte buehne" });
  const svg = s("svg", { viewBox: "0 0 330 150", preserveAspectRatio: "xMidYMid meet" });
  svg.style.aspectRatio = "330 / 150";
  const legende = el("div", { class: "legende" });
  const tonKnopf = el("button", { class: "tonknopf", title: "Ton ein- oder ausschalten" });
  const tonZeigen = () => { tonKnopf.textContent = TON.an() ? "🔊 Ton an" : "🔇 Ton aus"; };
  tonKnopf.addEventListener("click", () => { speicher.schreiben("ton", !TON.an()); tonZeigen(); });
  tonZeigen();
  box.append(svg, el("div", { class: "buehnenfuss" }, legende, tonKnopf));

  const BODEN = 128, M = 90;      // Boden in Pixeln, 90 Pixel je Meter
  const AUS = "#41474c";
  ["von der Seite", "von vorne", "von oben"].forEach((name, i) => {
    const t = s("text", { x: 55 + 110 * i, y: 145, "font-size": 9, fill: "#8a8f93", "text-anchor": "middle" });
    t.textContent = name; svg.append(t);
    if (i < 2) svg.append(s("line", { x1: 110 * i + 8, y1: BODEN, x2: 110 * i + 102, y2: BODEN, stroke: "#c4c8ca", "stroke-width": 1.5 }));
    if (i) svg.append(s("line", { x1: 110 * i, y1: 10, x2: 110 * i, y2: 135, stroke: "#e2e4e5", "stroke-width": 1 }));
  });
  const led = (cx, cy, r) => {
    const halo = s("circle", { cx, cy, r: r * 2.6, fill: "none", opacity: 0 });
    const kern = s("circle", { cx, cy, r, fill: AUS, stroke: "#24282b", "stroke-width": 0.6 });
    return { halo, kern };
  };
  const bein = () => s("polyline", { fill: "none", stroke: "#3a3f43", "stroke-width": 4, "stroke-linecap": "round", "stroke-linejoin": "round" });

  // von der Seite: Spot schaut nach rechts
  const seiteBeine = [bein(), bein()];
  const seite = s("g");
  const seiteLed = [led(39, -3, 2.6), led(-39, -3, 2.6)];
  seite.append(
    s("rect", { x: -38, y: -8, width: 76, height: 16, rx: 5, fill: "#f5c518", stroke: "#24282b", "stroke-width": 1.2 }),
    s("rect", { x: 26, y: -7, width: 14, height: 14, rx: 3, fill: "#24282b" }),
    ...seiteLed.flatMap((l) => [l.halo, l.kern]),
  );
  const note = s("text", { x: 0, y: 0, "font-size": 11, "font-weight": 700, fill: "#24282b", opacity: 0 });
  svg.append(...seiteBeine, seite, note);

  // von vorne: Spots linke Seite ist rechts im Bild
  const vorneBeine = [bein(), bein()];
  const vorne = s("g");
  const vorneLed = [led(-11, -1, 2.4), led(0, -1, 2.4), led(11, -1, 2.4)];
  vorne.append(
    s("rect", { x: -22, y: -8, width: 44, height: 16, rx: 5, fill: "#f5c518", stroke: "#24282b", "stroke-width": 1.2 }),
    ...vorneLed.flatMap((l) => [l.halo, l.kern]),
  );
  svg.append(...vorneBeine, vorne);

  // von oben: die Nase zeigt nach oben
  const oben = s("g");
  const obenLed = [led(0, -38, 2.6)];
  oben.append(
    s("rect", { x: -22, y: -38, width: 44, height: 76, rx: 6, fill: "#f5c518", stroke: "#24282b", "stroke-width": 1.2 }),
    s("rect", { x: -16, y: -40, width: 32, height: 12, rx: 3, fill: "#24282b" }),
    ...obenLed.flatMap((l) => [l.halo, l.kern]),
  );
  svg.append(s("line", { x1: 275, y1: 22, x2: 275, y2: 118, stroke: "#e2e4e5", "stroke-dasharray": "3 3" }), oben);

  const alleLeds = [...seiteLed, ...vorneLed, ...obenLed];

  function zeigen(z, t) {
    const { steh, pose, licht, ton } = z;
    const hoehe = 0.30 + 0.20 * steh + pose.height * steh;          // Körpermitte über dem Boden, m
    const pitch = -18 * (1 - steh) + pose.pitch;                      // sitzend: Heck unten, Nase oben
    const y = BODEN - hoehe * M;

    seite.setAttribute("transform", `translate(55,${y}) rotate(${pitch})`);
    const rad = (pitch * Math.PI) / 180, c = Math.cos(rad), sn = Math.sin(rad);
    const welt = (lx, ly) => [55 + lx * c - ly * sn, y + lx * sn + ly * c];
    [[28, 8, 83], [-28, 8, 25 - 4 * (1 - steh)]].forEach(([hx, hy, fuss], i) => {
      const [x0, y0] = welt(hx, hy);
      const kx = (x0 + fuss) / 2 - 7, ky = (y0 + BODEN) / 2;
      seiteBeine[i].setAttribute("points", `${x0},${y0} ${kx},${ky} ${fuss},${BODEN}`);
    });

    vorne.setAttribute("transform", `translate(165,${y}) rotate(${-pose.roll})`);
    const rr = (-pose.roll * Math.PI) / 180, rc = Math.cos(rr), rs = Math.sin(rr);
    [[-15, 8, 149], [15, 8, 181]].forEach(([hx, hy, fuss], i) => {
      const x0 = 165 + hx * rc - hy * rs, y0 = y + hx * rs + hy * rc;
      vorneBeine[i].setAttribute("points", `${x0},${y0} ${fuss},${BODEN}`);
    });

    oben.setAttribute("transform", `translate(275,70) rotate(${-pose.yaw})`);

    const farbe = licht ? `rgb(${licht.rgb.join(",")})` : null;
    const deckung = licht ? 0.45 + 0.55 * Math.min(1, licht.hell) : 0;
    alleLeds.forEach(({ halo, kern }) => {
      kern.setAttribute("fill", farbe || AUS);
      kern.setAttribute("fill-opacity", farbe ? 0.5 + 0.5 * Math.min(1, licht.hell * 2) : 1);
      halo.setAttribute("fill", farbe || "none");
      halo.setAttribute("opacity", deckung * 0.45);
    });

    if (ton) {
      const [nx, ny] = welt(30, -16);
      note.setAttribute("x", nx); note.setAttribute("y", ny);
      note.textContent = `♪ ${ton.note}${ton.octave}`;
      note.setAttribute("opacity", 1);
    } else note.setAttribute("opacity", 0);

    const lichtText = licht ? `${FARBNAMEN[licht.rgb.join(",")] || "rgb(" + licht.rgb.join(", ") + ")"} ${Math.round(licht.hell * 100)} %` : "aus";
    const g = (v) => `${Math.round(v)}°`;
    legende.textContent =
      `t = ${t.toFixed(1)} s   ${steh > 0.5 ? "steht" : "sitzt"}   Licht: ${lichtText}   Ton: ${ton ? ton.note + ton.octave : "–"}\n` +
      `roll ${g(pose.roll)}  pitch ${g(pose.pitch)}  yaw ${g(pose.yaw)}  height ${pose.height.toFixed(2)} m`;
  }
  zeigen(zustandBei([], 0), 0);
  return { box, zeigen, zuruecksetzen() { zeigen(zustandBei([], 0), 0); } };
}

// ================================================================ Ausführen

// Ein gemeinsamer Python-Worker für alle Codefelder (web/motor.js).
const MOTOR = {
  worker: null,
  bereit: false,
  wartend: new Map(),
  naechste: 1,
  zuhoerer: new Set(),

  _starten() {
    this.worker = new Worker("motor.js");
    this.worker.onmessage = (ev) => {
      const d = ev.data;
      if (d.art === "status") {
        if (d.text === "bereit") this.bereit = true;
        this.zuhoerer.forEach((f) => f(d.text));
        return;
      }
      const w = this.wartend.get(d.id);
      if (!w) return;
      this.wartend.delete(d.id);
      if (d.art === "ergebnis") w.ok(d.ergebnis);
      else w.nein(new Error(d.text));
    };
    this.worker.onerror = (e) => {
      const fehler = new Error(e.message || "Der Python-Worker ist abgestürzt.");
      this.wartend.forEach((w) => w.nein(fehler));
      this.wartend.clear();
    };
  },
  ausfuehren(auftrag) {
    if (!this.worker) this._starten();
    return new Promise((ok, nein) => {
      const id = this.naechste++;
      this.wartend.set(id, { ok, nein });
      this.worker.postMessage({ id, auftrag });
    });
  },
  vorwaermen() {
    if (this.worker) return;
    this.ausfuehren({ code: "", raum: "keiner" }).catch(() => {});
  },
  neustart() {
    if (this.worker) this.worker.terminate();
    this.worker = null;
    this.bereit = false;
    this.wartend.forEach((w) => w.nein(new Error("angehalten")));
    this.wartend.clear();
  },
  beiStatus(f) { this.zuhoerer.add(f); return () => this.zuhoerer.delete(f); },
};

const ICON = {
  play: '<svg viewBox="0 0 16 16"><path d="M4 2.5v11l9-5.5z"/></svg>',
  stopp: '<svg viewBox="0 0 16 16"><rect x="3.5" y="3.5" width="9" height="9"/></svg>',
  reset: '<svg viewBox="0 0 16 16"><path d="M8 2.5a5.5 5.5 0 1 1-5.2 3.7l1.6.6A3.8 3.8 0 1 0 8 4.2v2.3L4.6 3.4 8 .3z"/></svg>',
  laden: '<svg viewBox="0 0 16 16"><path d="M7 1.5h2v7l2.6-2.6 1.4 1.4L8 12.3 3 7.3l1.4-1.4L7 8.5zM2 13h12v2H2z"/></svg>',
};

function codeAusfuehrbar({ schluessel, code, raum, start, starts = null, ziele = null, beiErgebnis = null }) {
  MOTOR.vorwaermen();   // Python schon laden, während man liest
  const gespeichert = speicher.lesen("code:" + schluessel, null);
  const editor = editorBauen(gespeichert ?? code, {
    beiAenderung: (t) => speicher.schreiben("code:" + schluessel, t),
  });
  const konsole = el("div", { class: "konsole", html: '<span class="prompt">&gt;&gt;&gt;</span>' });
  const fehlerhilfe = el("div", { class: "fehlerhilfe", style: "display:none" });
  const bildleiste = el("div", { class: "bildleiste", style: "display:none" });
  const ergebnis = el("div", { class: "ergebnis" }, el("div", {}, konsole, fehlerhilfe, bildleiste));

  // Bilder, die das Programm selbst gespeichert hat (z. B. bild.save("vorne.png"))
  function bilderZeigen(laeufe) {
    bildleiste.innerHTML = "";
    const alle = laeufe.flatMap((l) => l.bilder || []);
    bildleiste.style.display = alle.length ? "" : "none";
    for (const b of alle) {
      const fig = el("figure", {});
      if (b.daten) fig.append(el("img", { src: b.daten, alt: b.name }));
      fig.append(el("figcaption", {}, b.name + (b.fehler ? ` (${b.fehler})` : "")));
      bildleiste.append(fig);
    }
  }
  const info = el("span", { class: "info" });

  let karte = null;
  const startliste = starts && starts.length ? starts : [start || ""];
  let startposen = [];
  if (raum === "keiner") raum = null;
  let buehne = null;
  if (raum === "trocken") {
    buehne = buehneBauen();
    ergebnis.classList.add("mitkarte");
    ergebnis.append(buehne.box);
  } else if (raum) {
    raumHolen(raum).then((r) => {
      if (!r) return;
      startposen = startliste.map((st) => (st ? st.split(",").map(Number) : r.start));
      karte = karteBauen(r, startposen);
      // Breite Räume (z. B. «Durchgang», 9 × 4 m) unter die Ausgabe, sonst werden sie winzig
      const g = r.groesse || [5, 4];
      if (g[0] / g[1] > 1.8) karte.box.classList.add("breit");
      else ergebnis.classList.add("mitkarte");
      ergebnis.append(karte.box);
    });
  }

  let aktiv = null;   // {abbrechen()} solange gerechnet oder abgespielt wird
  const knopfStart = el("button", { class: "knopf ausfuehren", title: "Ausführen (Strg+Enter)", html: ICON.play + "Ausführen" });
  const knopfReset = el("button", { class: "knopf", title: "Ursprünglichen Code wiederherstellen", html: ICON.reset });
  const knopfLaden = el("button", { class: "knopf", title: "Als .py-Datei herunterladen", html: ICON.laden });

  function laeuft(ja) {
    knopfStart.innerHTML = ja ? ICON.stopp + "Stopp" : ICON.play + "Ausführen";
    knopfStart.classList.toggle("stopp", ja);
    knopfStart.classList.toggle("ausfuehren", !ja);
  }

  function ausgabeText(lauf) {
    const roh = lauf.ausgabe || "";
    const tb = roh.indexOf("Traceback (most recent call last)");
    if (lauf.status !== "fehler" || tb < 0) return esc(roh);
    const f = lauf.fehler;
    return esc(roh.slice(0, tb)) +
      `<span class="fehlerzeile">${esc(f ? f.meldung : "Fehler")}</span>\n` +
      `<details class="ganzer-fehler"><summary>ganze Fehlermeldung anzeigen</summary>${esc(roh.slice(tb))}</details>`;
  }

  function konsoleZeigen(gruppe) {
    const mehrere = gruppe.laeufe.length > 1;
    let text = "";
    gruppe.laeufe.forEach((lauf, i) => {
      if (mehrere) {
        const farbe = SPURFARBEN[i % SPURFARBEN.length];
        text += `<span class="startkopf" style="color:${farbe}">── Start ${i + 1}${lauf.start ? ` bei (${esc(lauf.start)})` : ""} ──</span>\n`;
      }
      text += ausgabeText(lauf);
    });
    let fuss = "";
    if (gruppe.status === "spielt") fuss = `<span class="leise">▶ Spot-Zeit ${gruppe.jetzt.toFixed(1)} von ${gruppe.dauer} s · ${gruppe.tempo > 1 ? gruppe.tempo + "-fach schneller abgespielt" : "in Echtzeit"}</span>`;
    else if (gruppe.status === "fertig") fuss = `<span class="leise">— fertig nach ${gruppe.dauer} s Spot-Zeit</span>`;
    konsole.innerHTML = '<span class="prompt">&gt;&gt;&gt;</span> \n' + text + fuss;
    konsole.scrollTop = konsole.scrollHeight;
    const i = gruppe.laeufe.findIndex((l) => l.status === "fehler" && l.fehler);
    if (i >= 0) {
      const f = gruppe.laeufe[i].fehler;
      fehlerhilfe.style.display = "";
      fehlerhilfe.innerHTML = (mehrere ? `<b>Start ${i + 1}:</b> ` : "") +
        (f.zeile ? `<b>Fehler in Zeile ${f.zeile}</b>${f.code ? `: <code>${esc(f.code)}</code>` : ""}<br>` : "<b>Fehler</b><br>") +
        esc(f.meldung) + (f.hinweis ? `<br>👉 ${esc(f.hinweis)}` : "");
    } else {
      fehlerhilfe.style.display = "none";
    }
  }

  function hinweisZeigen(text) {
    konsole.innerHTML = `<span class="prompt">&gt;&gt;&gt;</span> <span class="leise">${esc(text)}</span>`;
  }

  // Erst rechnet Python im Browser (virtuelle Uhr, schnell), dann wird Spots
  // Weg abgespielt — schneller als echt, damit niemand eine Minute zuschaut.
  async function starten() {
    if (aktiv) { aktiv.abbrechen(); return; }
    document.dispatchEvent(new CustomEvent("neuer-lauf", { detail: schluessel }));
    if (karte) karte.zuruecksetzen(startposen);
    if (buehne) { buehne.zuruecksetzen(); TON.vorbereiten(); }   // Ton nur nach einem Klick erlaubt
    fehlerhilfe.style.display = "none";
    bilderZeigen([]);
    laeuft(true);

    let abgebrochen = false, wiedergabeEnde = null;
    aktiv = {
      abbrechen() {
        if (wiedergabeEnde) { wiedergabeEnde(); return; }   // beim Abspielen: zum Ende springen
        abgebrochen = true;
        MOTOR.neustart();                                     // beim Rechnen: Python anhalten
      },
    };
    const abmelden = MOTOR.beiStatus((text) => { if (text !== "bereit") hinweisZeigen(text); });
    hinweisZeigen(MOTOR.bereit ? "Spot rechnet …" : "Python wird gestartet …");

    const laeufe = [];
    try {
      for (const st of startliste) {
        if (startliste.length > 1) hinweisZeigen(`Spot rechnet: Start ${laeufe.length + 1} von ${startliste.length} …`);
        laeufe.push(await MOTOR.ausfuehren({ code: editor.wert(), raum: raum || "keiner", start: st, ziele }));
      }
    } catch (e) {
      abmelden(); aktiv = null; laeuft(false);
      hinweisZeigen(abgebrochen
        ? "Angehalten. (Python startet beim nächsten Ausführen neu.)"
        : "Python konnte nicht laufen: " + e.message);
      return;
    }
    abmelden();
    bilderZeigen(laeufe);

    const status = laeufe.some((l) => l.status === "abgebrochen") ? "abgebrochen"
      : laeufe.some((l) => l.status === "fehler") ? "fehler" : "fertig";
    const dauer = Math.max(0.1, ...laeufe.map((l) => l.dauer || 0));
    const tempo = Math.max(2, Math.ceil(dauer / 12));
    const gruppe = { laeufe, status: "spielt", dauer, tempo, jetzt: 0 };

    if (karte && laeufe.some((l) => l.weg.length > 1)) {
      await new Promise((fertig) => {
        const t0 = performance.now();
        let ende = false;
        wiedergabeEnde = () => { ende = true; };
        function bild() {
          const t = ende ? Infinity : ((performance.now() - t0) / 1000) * tempo;
          laeufe.forEach((l, i) => karte.zeigen(i, l.weg.filter((p) => p[0] <= t), t >= dauer ? l.angestossen : []));
          karte.menschBei(laeufe[0].mensch, t);
          gruppe.jetzt = Math.min(t, dauer);
          konsoleZeigen(gruppe);
          if (t >= dauer) { fertig(); return; }
          setTimeout(bild, 40);   // nicht requestAnimationFrame: das steht in verdeckten Tabs still
        }
        bild();
      });
    }
    if (karte) {
      laeufe.forEach((l, i) => karte.zeigen(i, l.weg, l.angestossen));
      karte.menschBei(laeufe[0] && laeufe[0].mensch, Infinity);
    }

    // Trockenlauf: Licht, Ton und Haltung in Echtzeit abspielen
    const sig = (buehne && laeufe[0] && laeufe[0].signale) || [];
    if (buehne && sig.length) {
      const endT = Math.max(dauer, ...sig.map((x) => x.t + (x.duration || 0)), sig[sig.length - 1].t + UEBERGANG_S);
      gruppe.tempo = 1;
      await new Promise((fertig) => {
        const t0 = performance.now();
        const gespielt = new Set();
        let ende = false;
        wiedergabeEnde = () => { ende = true; };
        function bild() {
          const t = ende ? endT : (performance.now() - t0) / 1000;
          if (!ende) {
            sig.forEach((x, i) => {
              if (x.art === "beep" && x.t <= t && !gespielt.has(i)) {
                gespielt.add(i);
                if (t < x.t + x.duration) TON.spielen(x.note, x.octave, x.t + x.duration - t);
              }
            });
          }
          buehne.zeigen(zustandBei(sig, t), Math.min(t, endT));
          gruppe.jetzt = Math.min(t, dauer);
          konsoleZeigen(gruppe);
          if (t >= endT) { fertig(); return; }
          setTimeout(bild, 40);
        }
        bild();
      });
    }
    gruppe.status = status;
    konsoleZeigen(gruppe);
    aktiv = null;
    laeuft(false);
    if (beiErgebnis) beiErgebnis(gruppe);
  }
  document.addEventListener("neuer-lauf", (e) => {
    if (e.detail !== schluessel && aktiv) aktiv.abbrechen();
  });

  knopfStart.addEventListener("click", starten);
  knopfReset.addEventListener("click", () => {
    if (confirm("Deine Änderungen an diesem Code verwerfen?")) {
      editor.setzen(code); speicher.loeschen("code:" + schluessel);
    }
  });
  knopfLaden.addEventListener("click", () => {
    const a = el("a", { href: URL.createObjectURL(new Blob([editor.wert()], { type: "text/x-python" })), download: "spot_programm.py" });
    a.click();
  });
  editor.textfeld.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); e.stopImmediatePropagation(); starten(); }
  }, true);

  if (raum === "trocken") info.textContent = "Trockenlauf · Spot als Zeichnung";
  else if (raum && raum.startsWith("kamera-")) info.textContent = "Kamera-Szene · aufgenommen im 3D-Übungsraum";
  else if (raum && raum.startsWith("mensch-")) info.textContent = "Simulator · ein Mensch mit Tag 9 geht mit";
  else if (raum) info.textContent = "Simulator · Raum «" + raum + "»";
  return el("div", { class: "codefeld" }, editor.huelle, el("div", { class: "knoepfe" }, info, knopfStart, knopfReset, knopfLaden), ergebnis);
}

// ================================================================ Quiz

// Volle Punkte nur beim ersten Versuch, beim zweiten die Hälfte, beim dritten keine:
// sonst gewinnt bei vier Antworten und drei Versuchen auch, wer nur rät.
function quizPunkte(punkte, fehlversuche) {
  return fehlversuche === 0 ? punkte : fehlversuche === 1 ? Math.floor(punkte / 2) : 0;
}

function quizBauen(block, schluessel) {
  const zustand = quizLesen(schluessel);
  const buchstaben = "ABCDEFGH";
  const box = el("div", { class: "quiz" });
  const frage = el("div", { class: "frage", html: markdown(block.frage) });
  const liste = el("div");
  const versuche = el("span", { class: "versuche" });
  const punkte = el("span", { class: "punkte" }, "Punkte");
  const erklaerung = el("div", { class: "erklaerung", style: "display:none" });
  const richtigIdx = block.antworten.findIndex((a) => a.richtig);
  const knoepfe = block.antworten.map((a, i) => {
    const k = el("button", { class: "antwort" },
      el("span", { class: "buchstabe" }, buchstaben[i]),
      el("span", { class: "atext", html: inline(a.text) }));
    k.addEventListener("click", () => waehlen(i));
    liste.append(k);
    return k;
  });

  function zeigen() {
    const ende = zustand.geloest || zustand.falsch.length >= 3;
    knoepfe.forEach((k, i) => {
      k.classList.toggle("falsch", zustand.falsch.includes(i));
      k.classList.toggle("richtig", ende && i === richtigIdx);
      k.classList.toggle("gedimmt", ende && i !== richtigIdx && !zustand.falsch.includes(i));
      k.disabled = ende || zustand.falsch.includes(i);
    });
    const uebrig = 3 - zustand.falsch.length;
    if (zustand.geloest) {
      const p = quizPunkte(block.punkte, zustand.falsch.length);
      versuche.textContent = zustand.falsch.length ? `Gelöst im ${zustand.falsch.length + 1}. Versuch.` : "Gleich beim ersten Versuch gelöst!";
      punkte.textContent = `+${p} Punkt${p === 1 ? "" : "e"}`;
      punkte.classList.toggle("erhalten", p > 0);
    } else if (ende) {
      versuche.textContent = "Drei Versuche sind aufgebraucht. Lies die Erklärung und probiere es im Code aus.";
      punkte.textContent = "0 Punkte";
    } else {
      versuche.textContent = zustand.falsch.length === 0
        ? "3 Versuche. Volle Punkte gibt es nur beim ersten — überleg zuerst, probier es vielleicht im Code aus."
        : `Noch ${uebrig} Versuch${uebrig === 1 ? "" : "e"}.`;
      punkte.textContent = "Punkte";
    }
    if (ende && block.erklaerung) {
      erklaerung.style.display = "";
      erklaerung.className = "erklaerung" + (zustand.geloest ? "" : " daneben");
      erklaerung.innerHTML = markdown(block.erklaerung);
    }
  }
  function waehlen(i) {
    if (zustand.geloest || zustand.falsch.length >= 3) return;
    if (i === richtigIdx) {
      zustand.geloest = true;
      punkteSetzen(schluessel, quizPunkte(block.punkte, zustand.falsch.length));
    } else {
      zustand.falsch.push(i);
    }
    quizSchreiben(schluessel, zustand);
    zeigen();
  }
  zeigen();
  box.append(frage, liste, el("div", { class: "quizfuss" }, versuche, punkte), erklaerung);
  return box;
}

// ================================================================ Aufgabe

function aufgabeBauen(block, schluessel) {
  const geschafft = (punkteLesen()[schluessel] || 0) > 0;
  const ziele = el("ul", { class: "zielliste" });
  const zielText = (z) => {
    const w = z.werte;
    switch (z.art) {
      case "ende_bei": return `Spot endet bei x = ${w[0]}, y = ${w[1]} (auf ${Math.round(w[2] * 100)} cm genau)`;
      case "ende_in": return `Spot endet im Bereich x ${w[0]}–${w[2]}, y ${w[1]}–${w[3]}`;
      case "blick": return `Spot schaut am Ende in Richtung ${w[0]}° (± ${w[1]}°)`;
      case "nicht_angestossen": return "Spot stösst nirgends an";
      case "ausgabe": return `In der Ausgabe steht «${w[0]}»`;
      case "aufgerufen": return `Das Programm benutzt ${w[0]}()`;
      case "gefahren": return `Spot legt mindestens ${w[0]} m zurück`;
      case "steht": return "Spot steht am Ende";
      case "sitzt": return "Spot sitzt am Ende";
      default: return z.art;
    }
  };
  block.ziele.forEach((z) => ziele.append(el("li", {}, zielText(z))));
  const tipp = el("div", { class: "tipp", style: "display:none" });
  const meldung = el("div", { class: "geschafft", style: geschafft ? "" : "display:none" }, "✓ Aufgabe gelöst");
  const punkte = el("span", { class: "punkte" + (geschafft ? " erhalten" : "") }, geschafft ? `+${block.punkte} Punkte` : `${block.punkte} Punkte`);
  let fehlversuche = 0;

  const mehrere = (block.starts || []).length > 1;
  const feld = codeAusfuehrbar({
    schluessel, code: block.code, raum: block.raum, start: block.start, starts: block.starts, ziele: block.ziele,
    beiErgebnis(z) {
      // Ein Ziel gilt nur, wenn es von JEDEM Startplatz aus erreicht ist.
      const proLauf = z.laeufe.map((l) => l.pruefung || []);
      const pr = (proLauf[0] || []).map((p, j) => {
        const daneben = proLauf.map((liste, i) => [i, liste[j]]).filter(([, q]) => q && !q.ok);
        const detail = mehrere
          ? daneben.map(([i, q]) => `Start ${i + 1}: ${q.detail || "nicht erfüllt"}`).join(" · ")
          : p.detail;
        return { text: p.text, ok: daneben.length === 0, detail: daneben.length ? detail : "" };
      });
      ziele.innerHTML = "";
      for (const p of pr) {
        ziele.append(el("li", { class: p.ok ? "ok" : "nein" }, p.text, p.detail ? el("span", { class: "detail" }, p.detail) : null));
      }
      if (pr.length && pr.every((p) => p.ok)) {
        meldung.style.display = "";
        meldung.className = "geschafft";
        meldung.textContent = "✓ Aufgabe gelöst";
        punkte.textContent = `+${block.punkte} Punkte`; punkte.classList.add("erhalten");
        punkteSetzen(schluessel, block.punkte);
        tipp.style.display = "none";
      } else if (z.status !== "abgebrochen") {
        if ((punkteLesen()[schluessel] || 0) > 0) {
          meldung.className = "geschafft frueher";
          meldung.textContent = "Schon einmal gelöst, die Punkte bleiben. Dieser Versuch erfüllt nicht alle Ziele.";
        }
        fehlversuche++;
        const t = block.tipps[Math.min(fehlversuche, block.tipps.length) - 1];
        if (t) { tipp.style.display = ""; tipp.innerHTML = "💡 " + inline(t); }
      }
    },
  });
  return el("div", { class: "aufgabe" },
    el("div", { class: "aufgabenkopf" }, el("b", {}, "Aufgabe"), punkte),
    el("div", {}, mehrere
      ? `Dein Programm läuft gleichzeitig von ${block.starts.length} Startplätzen aus. Es ist fertig, wenn von jedem aus gilt:`
      : "Dein Programm ist fertig, wenn:"),
    ziele, meldung, tipp, feld);
}

// ================================================================ Seiten

function uebersicht() {
  const app = document.getElementById("app");
  app.innerHTML = "";
  const zuletzt = speicher.lesen("zuletzt", null);
  const gitter = el("div", { class: "kapitelgitter" });
  for (const k of KURS.kapitel) {
    const tabelle = el("table", {}, el("tr", {}, el("th", {}, "Abschnitt"), el("th", {}, "Punkte")));
    let alleFertig = !k.bald;
    k.abschnitte.forEach((a, ai) => {
      const soll = moeglichePunkte(a), ist = erreichtePunkte(k.id, ai, a);
      if (soll && ist < soll) alleFertig = false;
      tabelle.append(el("tr", {}, el("td", {}, a.titel), el("td", { class: soll && ist >= soll ? "erledigt" : "" }, soll ? `${ist}/${soll}` : "")));
    });
    const inhalt = [
      el("div", { class: "zahl" }, k.nummer),
      el("div", { class: "kennung" }, `Kapitel ${k.nummer}`),
      el("h2", {}, k.titel),
      tabelle,
      k.bald ? el("div", { class: "baldtext" }, "Kommt bald") : null,
    ];
    const karte = k.bald
      ? el("div", { class: "kapitel bald" }, ...inhalt)
      : el("a", { class: "kapitel" + (alleFertig ? " fertig" : ""), href: `#/k/${k.id}/0` }, ...inhalt);
    gitter.append(karte);
  }
  app.append(el("div", { class: "uebersicht" },
    el("div", { class: "einleitung" },
      el("h1", {}, "Spot programmieren"),
      el("p", {}, "Lerne, den Roboterhund Spot mit Python und spotlab zu steuern — erst im Simulator, dann am echten Roboter. Am Ende baust du eigene Projekte: einen unbekannten Raum erkunden, ein Objekt finden, eine Karte aufnehmen."),
      zuletzt ? el("a", { class: "weitermachen", href: zuletzt }, "Weitermachen →")
              : el("a", { class: "weitermachen", href: `#/k/${KURS.kapitel[0].id}/0` }, "Los geht's →")),
    gitter));
  window.scrollTo(0, 0);
}

function lektion(kid, ai) {
  const ki = KURS.kapitel.findIndex((k) => k.id === kid);
  const k = KURS.kapitel[ki];
  if (!k || k.bald || !k.abschnitte[ai]) { location.hash = "#/"; return; }
  const a = k.abschnitte[ai];
  speicher.schreiben("zuletzt", `#/k/${kid}/${ai}`);
  const app = document.getElementById("app");
  app.innerHTML = "";

  const n = k.abschnitte.length;
  const pfad = el("div", { class: "pfad" },
    el("a", { href: "#/" }, "Kursübersicht"), el("span", { class: "trenner" }, ">"),
    el("a", { href: `#/k/${kid}/0` }, `Kapitel ${k.nummer}: ${k.titel}`), el("span", { class: "trenner" }, ">"),
    el("span", {}, a.titel));
  const fortschritt = el("div", { class: "fortschritt" },
    el("div", { class: "balken", style: `width:${((ai + 1) / n) * 100}%` }), el("span", {}, `${ai + 1}/${n}`));

  const inhalt = el("div");
  a.bloecke.forEach((b, bi) => {
    const schluessel = `${kid}/${ai}/${bi}`;
    if (b.art === "text") inhalt.append(el("div", { html: markdown(b.text) }));
    else if (b.art === "code") inhalt.append(codeAusfuehrbar({ schluessel, code: b.code, raum: b.raum, start: b.start }));
    else if (b.art === "zeigen") { const e = editorBauen(b.code, { nurLesen: true }); inhalt.append(el("div", { class: "codefeld" }, e.huelle)); }
    else if (b.art === "quiz") inhalt.append(quizBauen(b, schluessel));
    else if (b.art === "aufgabe") inhalt.append(aufgabeBauen(b, schluessel));
  });

  // Zurück / Weiter über Kapitelgrenzen hinweg
  const offen = KURS.kapitel.filter((x) => !x.bald);
  const oi = offen.findIndex((x) => x.id === kid);
  let zurueck = null, weiter = null;
  if (ai > 0) zurueck = `#/k/${kid}/${ai - 1}`;
  else if (oi > 0) zurueck = `#/k/${offen[oi - 1].id}/${offen[oi - 1].abschnitte.length - 1}`;
  if (ai < n - 1) weiter = `#/k/${kid}/${ai + 1}`;
  else if (oi < offen.length - 1) weiter = `#/k/${offen[oi + 1].id}/0`;
  else weiter = "#/";
  const nav = el("div", { class: "nav" },
    el("a", { href: zurueck || "#", class: zurueck ? "" : "leer" }, "Zurück"),
    el("a", { href: weiter }, weiter === "#/" ? "Zur Übersicht" : "Weiter"));

  app.append(pfad, el("div", { class: "lektion" },
    fortschritt, el("p", { class: "kapitelname" }, `Kapitel ${k.nummer}: ${k.titel}`),
    el("h1", {}, a.titel), inhalt, nav));
  window.scrollTo(0, 0);
}

function route() {
  if (!KURS) return;
  const m = location.hash.match(/^#\/k\/([\w-]+)\/(\d+)$/);
  if (m) lektion(m[1], Number(m[2]));
  else uebersicht();
  punktestandZeigen();
}

async function start() {
  try {
    const antwort = await fetch("kurs.json");
    const d = await antwort.json();
    if (d.fehler) throw new Error(d.fehler);
    KURS = d;
  } catch (e) {
    document.getElementById("app").innerHTML = `<div class="kursfehler">Der Kurs konnte nicht geladen werden:<br>${esc(e.message)}</div>`;
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}
start();
