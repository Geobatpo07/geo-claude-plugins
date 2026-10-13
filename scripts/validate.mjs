// Contrôle de cohérence du dépôt — usage : npm run validate
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const warnings = [];
const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const SEMVER = /^\d+\.\d+\.\d+$/;

const readJson = (p) => {
  try { return JSON.parse(readFileSync(p, "utf8")); }
  catch (e) { errors.push(`${p} : JSON invalide (${e.message})`); return null; }
};

function parseFrontmatter(text) {
  const m = text.replace(/^﻿/, "").match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return null;
  const fm = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_-]+):\s*(.*)$/);
    if (kv) fm[kv[1]] = kv[2].replace(/^["']|["']$/g, "").trim();
  }
  return fm;
}

const market = readJson(join(root, ".claude-plugin", "marketplace.json"));
if (market) {
  if (!KEBAB.test(market.name ?? "")) errors.push(`marketplace.json : nom "${market.name}" non kebab-case`);
  const seen = new Set();
  for (const p of market.plugins ?? []) {
    const label = `plugin "${p.name}"`;
    if (seen.has(p.name)) errors.push(`${label} : déclaré deux fois`);
    seen.add(p.name);
    if (!KEBAB.test(p.name ?? "")) errors.push(`${label} : nom non kebab-case`);
    if (!SEMVER.test(p.version ?? "")) errors.push(`${label} : version "${p.version}" non SemVer`);
    const dir = join(root, p.source ?? "");
    if (!existsSync(dir)) { errors.push(`${label} : source introuvable (${p.source})`); continue; }

    const manifest = readJson(join(dir, ".claude-plugin", "plugin.json"));
    if (manifest) {
      if (manifest.name !== p.name) errors.push(`${label} : plugin.json name = "${manifest.name}"`);
      if (manifest.version !== p.version)
        errors.push(`${label} : version marketplace (${p.version}) ≠ plugin.json (${manifest.version})`);
    }

    const skillsDir = join(dir, "skills");
    if (!existsSync(skillsDir)) { warnings.push(`${label} : aucun dossier skills/`); continue; }
    for (const s of readdirSync(skillsDir)) {
      const sDir = join(skillsDir, s);
      if (!statSync(sDir).isDirectory()) continue;
      const sLabel = `skill "${p.name}/${s}"`;
      const file = join(sDir, "SKILL.md");
      if (!existsSync(file)) { errors.push(`${sLabel} : SKILL.md manquant`); continue; }
      const text = readFileSync(file, "utf8");
      const fm = parseFrontmatter(text);
      if (!fm) { errors.push(`${sLabel} : frontmatter manquant`); continue; }
      if (fm.name !== s) errors.push(`${sLabel} : name "${fm.name}" ≠ nom du dossier`);
      if (!KEBAB.test(fm.name ?? "") || fm.name.length > 64) errors.push(`${sLabel} : name invalide`);
      if (!fm.description) errors.push(`${sLabel} : description manquante`);
      else if (fm.description.length > 1024) errors.push(`${sLabel} : description > 1024 caractères`);
      const lines = text.split(/\r?\n/).length;
      if (lines > 300) warnings.push(`${sLabel} : ${lines} lignes (> 300, déplacer vers references/)`);
      for (const ref of text.matchAll(/\]\((references\/[^)#\s]+)\)/g)) {
        if (!existsSync(join(sDir, ref[1]))) errors.push(`${sLabel} : lien cassé ${ref[1]}`);
      }
    }
  }
}

for (const w of warnings) console.warn(`⚠  ${w}`);
for (const e of errors) console.error(`✖  ${e}`);
if (errors.length) { console.error(`\n${errors.length} erreur(s).`); process.exit(1); }
console.log(`✔  Dépôt valide${warnings.length ? ` (${warnings.length} avertissement(s))` : ""}.`);
