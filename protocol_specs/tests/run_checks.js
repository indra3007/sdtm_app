// Headless check runner for the protocol spec pages.
// Loads a page in jsdom, lets its scripts run, and prints the spec-check summary
// and any failing derivation tests. Exits non-zero if a check fails or a script errors.
//
//   npm install jsdom@24
//   node protocol_specs/tests/run_checks.js protocol_specs/dapa-hf.html
const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs");

const file = process.argv[2];
if (!file) { console.error("usage: node run_checks.js <page.html>"); process.exit(2); }

let errors = 0;
const vc = new VirtualConsole();
vc.on("jsdomError", e => { errors++; console.error("SCRIPT ERROR:", e.message); });

const dom = new JSDOM(fs.readFileSync(file, "utf8"), {
  runScripts: "dangerously", url: "https://localhost/", virtualConsole: vc, pretendToBeVisual: true,
});
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

setTimeout(() => {
  const d = dom.window.document;
  const text = el => el.textContent.replace(/\s+/g, " ").trim();
  const checks = [...d.querySelectorAll("#lintList .lint")].map(text);
  const fails = checks.filter(c => c.startsWith("fail"));
  console.log(`${file}: ${checks.length} checks, ${fails.length} failing, ${errors} script errors`);
  checks.forEach(c => console.log("  " + c.slice(0, 160)));
  process.exit(fails.length || errors ? 1 : 0);
}, 1500);
