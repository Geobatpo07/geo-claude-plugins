// Incrémente la version (plugin.json) des plugins dont le contenu a changé entre deux révisions
// sans que leur version ait été modifiée. Usage : node scripts/bump-versions.mjs <base> [head]
// Niveau déduit des messages de commit : `!:` / BREAKING CHANGE → majeur, `feat` → mineur, sinon patch.
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const git = (...args) => execFileSync("git", args, { cwd: root, encoding: "utf8" });
const head = process.argv[3] || "HEAD";
let base = process.argv[2];
if (!base || /^0+$/.test(base)) base = `${head}~1`;
try { git("rev-parse", "--verify", base); } catch { console.log("Pas de révision de base : rien à faire."); process.exit(0); }

const changed = git("diff", "--name-only", base, head).split("\n").filter(Boolean);
const log = git("log", "--format=%s%n%b%x00", `${base}..${head}`).split("\0");

const levelOf = (dir) => {
  const msgs = log.filter((m) => m.trim());
  if (msgs.some((m) => /BREAKING CHANGE|^\w+(\([^)]*\))?!:/m.test(m))) return "major";
  if (msgs.some((m) => /^feat(\(|:)/m.test(m))) return "minor";
  return "patch";
};

const bump = (v, level) => {
  const [maj, min, pat] = v.split(".").map(Number);
  return level === "major" ? `${maj + 1}.0.0` : level === "minor" ? `${maj}.${min + 1}.0` : `${maj}.${min}.${pat + 1}`;
};

for (const dir of readdirSync(join(root, "plugins"))) {
  const prefix = `plugins/${dir}/`;
  const manifestRel = `${prefix}.claude-plugin/plugin.json`;
  const manifestPath = join(root, manifestRel);
  if (!existsSync(manifestPath)) continue;
  const contentChanged = changed.some((f) => f.startsWith(prefix) && f !== manifestRel);
  if (!contentChanged) continue;

  let before = null;
  try { before = JSON.parse(git("show", `${base}:${manifestRel}`)).version; } catch { /* nouveau plugin */ }
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  if (before === null || manifest.version !== before) {
    console.log(`${manifest.name} : version déjà gérée (${manifest.version}).`);
    continue;
  }
  const level = levelOf(dir);
  const next = bump(manifest.version, level);
  writeFileSync(manifestPath, readFileSync(manifestPath, "utf8").replace(/("version"\s*:\s*")[^"]+(")/, `$1${next}$2`));
  console.log(`${manifest.name} : ${manifest.version} → ${next} (${level})`);
}
