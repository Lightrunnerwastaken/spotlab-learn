// Web Worker: Python (Pyodide) mit dem echten spotlab-Simulator, im Browser der Schüler.
//
// Einmal beim ersten Lauf: Pyodide laden, numpy/protobuf dazu, bosdyn von PyPI
// (nicht frei lizenziert, darum nicht in unserem Zip), dann spotlab + Kursmotor
// aus py/kurs-python.zip. Danach rechnet jeder Lauf in Sekundenbruchteilen bis
// wenigen Sekunden, weil der Kursmotor eine virtuelle Uhr benutzt.
//
// Nachrichten hinein:  {id, auftrag: {code, raum, start, ziele}}
// Nachrichten hinaus:  {art: "status", text} | {art: "ergebnis", id, ergebnis} | {art: "fehler", id, text}

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
importScripts(PYODIDE + "pyodide.js");

const BOSDYN = [
  "bosdyn-api==5.0.1.2",
  "bosdyn-client==5.0.1.2",
  "bosdyn-core==5.0.1.2",
  "Deprecated==1.2.18",
];

let bereit = null;
let laufeJson = null;

function melde(text) { postMessage({ art: "status", text }); }

async function laden() {
  melde("Python wird geladen (nur beim ersten Mal, etwa 10–20 s) …");
  const py = await loadPyodide({ indexURL: PYODIDE });
  melde("numpy und protobuf werden geladen …");
  await py.loadPackage(["numpy", "protobuf", "micropip", "wrapt"]);
  melde("Spot-SDK (bosdyn) wird geladen …");
  const micropip = py.pyimport("micropip");
  await micropip.install.callKwargs(BOSDYN, { deps: false });
  melde("spotlab wird geladen …");
  const antwort = await fetch(new URL("py/kurs-python.zip", self.location.href));
  if (!antwort.ok) throw new Error("py/kurs-python.zip fehlt (" + antwort.status + ")");
  py.unpackArchive(await antwort.arrayBuffer(), "zip", { extractDir: "/home/pyodide/kurs" });
  py.runPython(`
import sys
sys.path.insert(0, "/home/pyodide/kurs")
import kursmotor
kursmotor.installieren()
import spotlab.backends.sim  # einmal vorab, damit der erste Lauf nicht wartet
`);
  laufeJson = py.pyimport("kursmotor").lauf_json;
  melde("bereit");
  return py;
}

self.onmessage = async (ev) => {
  const { id, auftrag } = ev.data;
  try {
    if (!bereit) bereit = laden();
    await bereit;
    const ergebnis = JSON.parse(laufeJson(JSON.stringify(auftrag)));
    postMessage({ art: "ergebnis", id, ergebnis });
  } catch (e) {
    bereit = null;   // beim nächsten Versuch neu laden
    postMessage({ art: "fehler", id, text: String(e && e.message ? e.message : e) });
  }
};
