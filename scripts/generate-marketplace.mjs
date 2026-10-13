// Régénère .claude-plugin/marketplace.json depuis plugins/*/.claude-plugin/plugin.json
// Usage : npm run generate   (ou --check pour échouer si le fichier est désynchronisé)
import { readFileSync, writeFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const target = join(root, ".claude-plugin", "marketplace.json");
const pluginsDir = join(root, "plugins");

// L'en-tête (name, owner, metadata) reste la source de vérité dans marketplace.json ;
// seule la liste `plugins` est générée.
const current = JSON.parse(readFileSync(target, "utf8"));

const plugins = [];
for (const dir of readdirSync(pluginsDir).sort()) {
  const manifestPath = join(pluginsDir, dir, ".claude-plugin", "plugin.json");
  if (!statSync(join(pluginsDir, dir)).isDirectory() || !existsSync(manifestPath)) continue;
  const m = JSON.parse(readFileSync(manifestPath, "utf8"));
  const entry = { name: m.name, source: `./plugins/${dir}`, description: m.description, version: m.version };
  if (m.keywords?.length) entry.keywords = m.keywords;
  plugins.push(entry);
}

const next = { ...current, plugins };
// Un tableau de chaînes reste sur une ligne, comme dans le fichier édité à la main.
const output = JSON.stringify(next, null, 2)
  .replace(/\[\s+((?:"[^"\n]*",?\s+)+)\]/g, (_, items) =>
    `[${items.trim().replace(/,\s+/g, ", ")}]`) + "\n";

if (process.argv.includes("--check")) {
  if (readFileSync(target, "utf8").replace(/\r\n/g, "\n") !== output) {
    console.error("✖  marketplace.json désynchronisé — lancer `npm run generate`.");
    process.exit(1);
  }
  console.log("✔  marketplace.json à jour.");
} else {
  writeFileSync(target, output);
  console.log(`✔  marketplace.json généré (${plugins.length} plugin(s)).`);
}
