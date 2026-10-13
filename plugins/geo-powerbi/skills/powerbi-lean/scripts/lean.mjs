#!/usr/bin/env node
// powerbi-lean — analyse en lecture seule d'un projet PBIP (TMDL + PBIR).
// Usage :
//   node lean.mjs audit  <dossier PBIP | *.SemanticModel> [--changed] [--json]
//   node lean.mjs usage  <dossier PBIP | *.SemanticModel> [--field "Table[Nom]"] [--json]
// Aucun fichier n'est modifié. Node 18+ ; aucune dépendance.
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, basename, dirname, resolve, relative, sep } from "node:path";
import { execFileSync } from "node:child_process";

// ───────────────────────── utilitaires ─────────────────────────
const read = (p) => readFileSync(p, "utf8").replace(/^\uFEFF/, "").replace(/\r\n/g, "\n");
const walk = (dir, filter, out = []) => {
  if (!existsSync(dir)) return out;
  for (const e of readdirSync(dir)) {
    if (e === ".pbi" || e === ".git" || e === "node_modules") continue;
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p, filter, out);
    else if (filter(p)) out.push(p);
  }
  return out;
};
const unquote = (s) => (s && s.startsWith("'") && s.endsWith("'") ? s.slice(1, -1).replace(/''/g, "'") : s);
const key = (t, n) => `${t}[${n}]`;
const lc = (s) => s.toLowerCase();

// ───────────────────────── localisation ─────────────────────────
function locate(arg) {
  let p = resolve(arg || ".");
  let sm = null;
  if (p.endsWith(".SemanticModel")) sm = p;
  else if (p.endsWith(".pbip")) p = dirname(p);
  if (!sm) {
    const cands = readdirSync(p).filter((d) => d.endsWith(".SemanticModel"));
    if (!cands.length) throw new Error(`Aucun dossier *.SemanticModel dans ${p}`);
    sm = join(p, cands[0]);
  }
  const parent = dirname(sm);
  const prefix = basename(sm).replace(/\.SemanticModel$/, "");
  const reports = readdirSync(parent).filter((d) => d.endsWith(".Report"));
  const rep = reports.includes(`${prefix}.Report`) ? `${prefix}.Report` : reports[0];
  return { root: parent, model: join(sm, "definition"), report: rep ? join(parent, rep, "definition") : null };
}

// ───────────────────────── parseur TMDL ─────────────────────────
const NAME = String.raw`'(?:[^']|'')+'|[^\s=:'][^=:]*?`;
const OBJ = new RegExp(String.raw`^([A-Za-z]+)\s+(${NAME})\s*(?:=\s*(.*))?$`);
const PROP_EXPR = /^([A-Za-z]+)\s*=\s*(.*)$/;
const PROP = /^([A-Za-z]+)\s*:\s*(.*)$/;
const BARE = /^([A-Za-z]+)$/;
const OBJECT_KINDS = new Set(["table", "column", "measure", "partition", "hierarchy", "level", "calculationGroup",
  "calculationItem", "role", "tablePermission", "relationship", "expression", "annotation", "extendedProperty",
  "perspective", "culture", "model", "database", "ref", "dataSource", "linguisticMetadata", "columnPermission"]);

function parseTmdl(text) {
  const lines = text.split("\n");
  const root = { kind: "root", children: [], level: -1, props: {} };
  const stack = [root];
  let desc = [];
  const indent = (l) => (l.match(/^\t*/)[0].length);
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const t = raw.trim();
    if (!t) continue;
    const lvl = indent(raw);
    if (t.startsWith("///")) { desc.push(t.slice(3).trim()); continue; }
    while (stack.length > 1 && stack[stack.length - 1].level >= lvl) stack.pop();
    const parent = stack[stack.length - 1];
    // collecte d'une expression multiligne
    const collect = (first) => {
      const buf = [];
      if (first === "```") {
        for (i++; i < lines.length && lines[i].trim() !== "```"; i++) buf.push(lines[i]);
        return buf.join("\n");
      }
      if (first) buf.push(first);
      while (i + 1 < lines.length) {
        const nx = lines[i + 1];
        if (nx.trim() === "") { buf.push(""); i++; continue; }
        if (indent(nx) >= lvl + 2) { buf.push(nx); i++; } else break;
      }
      return buf.join("\n").trim();
    };
    let m;
    if ((m = t.match(OBJ)) && OBJECT_KINDS.has(m[1]) && !PROP.test(t.replace(/'(?:[^']|'')+'/g, "x"))) {
      const node = { kind: m[1], name: unquote(m[2].trim()), level: lvl, props: {}, children: [], desc: desc.join("\n") };
      if (m[3] !== undefined) node.expr = collect(m[3].trim());
      parent.children.push(node); stack.push(node); desc = []; continue;
    }
    desc = [];
    if ((m = t.match(PROP_EXPR)) && !t.includes(":")) { parent.props[m[1]] = collect(m[2].trim()); continue; }
    if ((m = t.match(PROP))) { parent.props[m[1]] = m[2].trim(); continue; }
    if ((m = t.match(BARE))) {
      if (OBJECT_KINDS.has(m[1])) { const node = { kind: m[1], name: "", level: lvl, props: {}, children: [] }; parent.children.push(node); stack.push(node); }
      else parent.props[m[1]] = true;
      continue;
    }
    if ((m = t.match(PROP_EXPR))) parent.props[m[1]] = collect(m[2].trim());
  }
  return root;
}

function loadModel(dir) {
  const model = { tables: new Map(), measures: new Map(), relationships: [], roles: [], files: new Map() };
  const files = walk(dir, (p) => p.endsWith(".tmdl"));
  for (const f of files) {
    const tree = parseTmdl(read(f));
    for (const n of tree.children) {
      if (n.kind === "table") {
        const tb = { name: n.name, desc: n.desc, props: n.props, file: f, columns: new Map(), measures: new Map(),
          hierarchies: [], partitions: [], calcGroup: null };
        for (const c of n.children) {
          if (c.kind === "column") tb.columns.set(c.name, { name: c.name, expr: c.expr, props: c.props, desc: c.desc });
          else if (c.kind === "measure") {
            const ms = { name: c.name, table: n.name, expr: c.expr || "", props: c.props, desc: c.desc, file: f };
            tb.measures.set(c.name, ms); model.measures.set(lc(c.name), ms);
          } else if (c.kind === "hierarchy") tb.hierarchies.push({ name: c.name, levels: c.children.filter((l) => l.kind === "level").map((l) => ({ name: l.name, column: unquote(l.props.column) })) });
          else if (c.kind === "partition") tb.partitions.push({ name: c.name, type: (c.expr || "").trim(), source: c.props.source || "" });
          else if (c.kind === "calculationGroup") tb.calcGroup = c.children.filter((x) => x.kind === "calculationItem").map((x) => ({ name: x.name, expr: x.expr || "" }));
        }
        model.tables.set(n.name, tb);
        model.files.set(f, n.name);
      } else if (n.kind === "relationship") {
        const sp = (s) => { const mm = (s || "").match(/^('(?:[^']|'')+'|[^.]+)\.(.+)$/); return mm ? [unquote(mm[1]), unquote(mm[2])] : [null, null]; };
        model.relationships.push({ name: n.name, from: sp(n.props.fromColumn), to: sp(n.props.toColumn), props: n.props, file: f });
      } else if (n.kind === "role") {
        model.roles.push({ name: n.name, perms: n.children.filter((c) => c.kind === "tablePermission").map((c) => ({ table: c.name, expr: c.expr || "" })), file: f });
      }
    }
  }
  return model;
}

// ───────────────────────── DAX ─────────────────────────
function stripDax(expr, keepStrings = false) {
  let out = "", i = 0;
  while (i < expr.length) {
    const c = expr[i], n = expr[i + 1];
    if (c === '"') { let j = i + 1; while (j < expr.length) { if (expr[j] === '"' && expr[j + 1] === '"') j += 2; else if (expr[j] === '"') break; else j++; } out += keepStrings ? expr.slice(i, j + 1) : '""'; i = j + 1; continue; }
    if (c === "'") { let j = i + 1; while (j < expr.length) { if (expr[j] === "'" && expr[j + 1] === "'") j += 2; else if (expr[j] === "'") break; else j++; } out += expr.slice(i, j + 1); i = j + 1; continue; }
    if (c === "[") { const j = expr.indexOf("]", i); out += expr.slice(i, j < 0 ? expr.length : j + 1); i = j < 0 ? expr.length : j + 1; continue; }
    if ((c === "/" && n === "/") || (c === "-" && n === "-")) { const j = expr.indexOf("\n", i); i = j < 0 ? expr.length : j; continue; }
    if (c === "/" && n === "*") { const j = expr.indexOf("*/", i + 2); i = j < 0 ? expr.length : j + 2; continue; }
    out += c; i++;
  }
  return out;
}
const TBL = String.raw`'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_]*`;
function daxRefs(expr, model) {
  const code = stripDax(expr || "");
  const cols = new Set(), measures = new Set(), tables = new Set();
  const qualified = new RegExp(String.raw`(${TBL})\s*\[([^\]]+)\]`, "g");
  let rest = code.replace(qualified, (_, t, n) => {
    const tn = unquote(t), tb = model.tables.get(tn);
    if (tb) { tables.add(tn); if (tb.columns.has(n)) cols.add(key(tn, n)); else if (model.measures.has(lc(n))) measures.add(lc(n)); }
    return " ";
  });
  rest.replace(/\[([^\]]+)\]/g, (_, n) => { if (model.measures.has(lc(n))) measures.add(lc(n)); return " "; });
  for (const tn of model.tables.keys()) {
    const q = tn.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (new RegExp(String.raw`(^|[^\w'])('${q.replace(/'/g, "''")}'|${/^[A-Za-z_]\w*$/.test(tn) ? q : "(?!)"})(?![\w\[])`).test(rest)) tables.add(tn);
  }
  return { cols, measures, tables, code };
}

// ───────────────────────── PBIR ─────────────────────────
function loadReport(dir, model) {
  const refs = []; // {table, name, kind, page, visual, file}
  if (!dir) return { refs, pages: new Map() };
  const pages = new Map();
  for (const f of walk(join(dir, "pages"), (p) => basename(p) === "page.json")) {
    try { const j = JSON.parse(read(f)); pages.set(basename(dirname(f)), j.displayName || basename(dirname(f))); } catch {}
  }
  for (const f of walk(dir, (p) => p.endsWith(".json"))) {
    let j; try { j = JSON.parse(read(f)); } catch { continue; }
    const rel = relative(dir, f).split(sep);
    const pi = rel.indexOf("pages"), vi = rel.indexOf("visuals");
    const page = pi >= 0 && rel[pi + 1] && rel[pi + 1] !== "pages.json" ? pages.get(rel[pi + 1]) || rel[pi + 1] : "(rapport)";
    const visual = vi >= 0 ? `${j.visual?.visualType || "visuel"} ${rel[vi + 1]}` : basename(f);
    const visit = (node, aliases) => {
      if (Array.isArray(node)) { node.forEach((x) => visit(x, aliases)); return; }
      if (!node || typeof node !== "object") return;
      let al = aliases;
      if (Array.isArray(node.From)) { al = new Map(aliases); for (const fr of node.From) if (fr.Name && fr.Entity) al.set(fr.Name, fr.Entity); }
      const ent = (e) => e?.SourceRef?.Entity || (e?.SourceRef?.Source && al.get(e.SourceRef.Source));
      for (const k of ["Measure", "Column"]) {
        const v = node[k];
        if (v && v.Property && v.Expression) { const t = ent(v.Expression); if (t) refs.push({ table: t, name: v.Property, kind: k, page, visual, file: f }); }
      }
      if (node.HierarchyLevel?.Expression?.Hierarchy) {
        const h = node.HierarchyLevel.Expression.Hierarchy, t = ent(h.Expression), tb = t && model.tables.get(t);
        const lvl = tb?.hierarchies.find((x) => x.name === h.Hierarchy)?.levels.find((l) => l.name === node.HierarchyLevel.Level);
        if (t) refs.push({ table: t, name: lvl?.column || node.HierarchyLevel.Level, kind: "Column", page, visual, file: f });
      }
      for (const v of Object.values(node)) visit(v, al);
    };
    visit(j, new Map());
  }
  return { refs, pages };
}

// ───────────────────────── graphe d'utilisation ─────────────────────────
function usage(model, report) {
  const usedM = new Set(), usedC = new Set(), why = new Map();
  const note = (k, r) => { if (!why.has(k)) why.set(k, []); why.get(k).push(r); };
  const queue = [];
  const useM = (n, r) => { const k = lc(n); if (!model.measures.has(k)) return; note("M:" + k, r); if (!usedM.has(k)) { usedM.add(k); queue.push(["M", k]); } };
  const useC = (t, n, r) => { const tb = model.tables.get(t); if (!tb?.columns.has(n)) return; const k = key(t, n); note("C:" + k, r); if (!usedC.has(k)) { usedC.add(k); queue.push(["C", k]); } };
  const fromDax = (expr, r) => { const d = daxRefs(expr, model); d.measures.forEach((m) => useM(model.measures.get(m).name, r)); d.cols.forEach((c) => { const [, t, n] = c.match(/^(.*)\[(.*)\]$/); useC(t, n, r); }); };
  for (const r of report.refs) {
    const label = `rapport : ${r.page} / ${r.visual}`;
    if (r.kind === "Measure") useM(r.name, label); else useC(r.table, r.name, label);
  }
  for (const rel of model.relationships) { if (rel.from[0]) useC(rel.from[0], rel.from[1], "relation"); if (rel.to[0]) useC(rel.to[0], rel.to[1], "relation"); }
  for (const ro of model.roles) for (const p of ro.perms) fromDax(p.expr, `rôle ${ro.name}`);
  for (const tb of model.tables.values()) {
    for (const p of tb.partitions) if (/^calculated/i.test(p.type)) fromDax(p.source, `table calculée ${tb.name}`);
    for (const ci of tb.calcGroup || []) fromDax(ci.expr, `groupe de calcul ${tb.name}`);
    if (tb.props.dataCategory === "Time") for (const c of tb.columns.values()) if (c.props.isKey) useC(tb.name, c.name, "clé de la table de dates");
  }
  while (queue.length) {
    const [kind, k] = queue.shift();
    if (kind === "M") { const m = model.measures.get(k); fromDax(m.expr, `mesure [${m.name}]`); if (m.props.formatStringDefinition) fromDax(m.props.formatStringDefinition, `format de [${m.name}]`); }
    else {
      const [, t, n] = k.match(/^(.*)\[(.*)\]$/); const c = model.tables.get(t).columns.get(n);
      if (c.expr) fromDax(c.expr, `colonne calculée ${k}`);
      if (c.props.sortByColumn) useC(t, unquote(c.props.sortByColumn), `tri de ${k}`);
    }
  }
  return { usedM, usedC, why };
}

// ───────────────────────── audit ─────────────────────────
const RULES = {
  dateDure: { re: /\bDATE\s*\(\s*\d{4}\s*,/i, label: "Date codée en dur (DATE(aaaa, …))" },
  dateSysteme: { re: /\b(TODAY|NOW|UTCTODAY|UTCNOW)\s*\(\s*\)/i, label: "Date système (TODAY/NOW) : résultat non reproductible" },
  iferror: { re: /\b(IFERROR|ISERROR)\s*\(/i, label: "IFERROR / ISERROR" },
  division: { re: /[\w\])]\s*\/\s*[A-Za-z_(\[']/, label: "Division « / » par une expression au lieu de DIVIDE" },
};

function audit(model, report, opts) {
  const { usedM, usedC } = usage(model, report);
  const findings = []; // {prio, cat, obj, detail, file}
  const add = (prio, cat, obj, detail, file) => findings.push({ prio, cat, obj, detail, file });
  const tableNames = [...model.tables.keys()];
  const relTables = new Set(model.relationships.flatMap((r) => [r.from[0], r.to[0]]));

  // mesures
  const byNorm = new Map();
  for (const m of model.measures.values()) {
    const obj = `[${m.name}] (${m.table})`;
    const code = stripDax(m.expr);
    const hidden = !!m.props.isHidden;
    if (!usedM.has(lc(m.name))) add(hidden ? 2 : 2, "Inutilisée", obj, `Mesure${hidden ? " masquée" : ""} jamais utilisée par le rapport ni par une autre mesure`, m.file);
    for (const r of Object.values(RULES)) { const mm = code.match(r.re); if (mm) add(r === RULES.iferror || r === RULES.dateSysteme ? 2 : 3, "Valeur en dur / risque", obj, `${r.label} — « ${mm[0].trim()} »`, m.file); }
    // valeurs en dur comparées à des colonnes de tables reliées (les tables déconnectées / paramètres sont ignorées)
    const withStr = stripDax(m.expr, true);
    const colCmp = new RegExp(String.raw`(${TBL})\s*\[([^\]]+)\]\s*(=|<>|IN)\s*(\{[^}]*\}|"[^"]*"|-?\d+)`, "gi");
    for (const mm of withStr.matchAll(colCmp)) {
      const tn = unquote(mm[1]);
      if (!model.tables.has(tn) || !relTables.has(tn)) continue;
      const lit = mm[4];
      if (/^-?\d$/.test(lit)) continue; // 0..9 : souvent des drapeaux
      add(3, "Valeur en dur / risque", obj, `${lit.startsWith('"') ? "Libellé" : lit.startsWith("{") ? "Liste de valeurs" : "Valeur numérique"} en dur comparé(e) à ${tn}[${mm[2]}] — « ${mm[0].slice(0, 80)} » : passer par une mesure ou une table de référence`, m.file);
    }
    for (const tn of tableNames) {
      const q = tn.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/'/g, "''");
      const re = new RegExp(String.raw`\bFILTER\s*\(\s*('${q}'${/^[A-Za-z_]\w*$/.test(tn) ? "|" + q : ""})\s*,`, "i");
      if (re.test(code)) add(2, "DAX", obj, `FILTER sur la table entière ${tn} : préférer un filtre de colonne ou VALUES/ALL sur la colonne`, m.file);
    }
    if (!hidden && !m.desc) add(3, "Documentation", obj, "Mesure visible sans description", m.file);
    if (!hidden && !m.props.formatString && !m.props.formatStringDefinition && !/""/.test(code)) add(3, "Documentation", obj, "Mesure visible sans format", m.file);
    const norm = lc(stripDax(m.expr, true)).replace(/\s+/g, "");
    if (norm.length > 12) { if (!byNorm.has(norm)) byNorm.set(norm, []); byNorm.get(norm).push(m); }
  }
  for (const grp of byNorm.values()) if (grp.length > 1)
    add(1, "Doublon", grp.map((m) => `[${m.name}]`).join(", "), "Expressions DAX identiques (hors commentaires et espaces) : garder une mesure, faire référencer les autres", grp[0].file);

  // colonnes
  const relCols = new Set(model.relationships.flatMap((r) => [key(r.from[0], r.from[1]), key(r.to[0], r.to[1])]));
  const idLike = /(^|[\s_])(id|key|cle|clé|code|annee|année|year|mois|month|trimestre|quarter|num|no|numero|numéro)([\s_]|$)|(id|key)$/i;
  let hasDateTable = false;
  for (const tb of model.tables.values()) {
    if (tb.props.dataCategory === "Time") hasDateTable = true;
    const inRel = model.relationships.some((r) => r.from[0] === tb.name || r.to[0] === tb.name);
    const isMeasureTable = tb.measures.size > 0 && [...tb.columns.values()].every((c) => c.props.isHidden);
    if (!inRel && !tb.calcGroup && !isMeasureTable)
      add(3, "Structure", tb.name, "Table sans relation (normal pour un paramètre / une table déconnectée ; sinon à vérifier)", tb.file);
    for (const c of tb.columns.values()) {
      const k = key(tb.name, c.name);
      if (!usedC.has(k) && !relCols.has(k) && !isMeasureTable)
        add(2, "Inutilisée", k, `Colonne${c.props.isHidden ? " masquée" : ""} jamais utilisée (rapport, DAX, relations, tri) : candidate à la suppression`, tb.file);
      if (/^sum$/i.test(c.props.summarizeBy || "") && idLike.test(c.name.replace(/([a-z])([A-Z])/g, "$1 $2")))
        add(2, "Modèle", k, "summarizeBy: sum sur une colonne qui ressemble à un identifiant / une année : mettre none", tb.file);
      if (relCols.has(k) && !c.props.isHidden && model.relationships.some((r) => key(r.from[0], r.from[1]) === k))
        add(3, "Modèle", k, "Clé étrangère visible : la masquer", tb.file);
    }
  }
  if (!hasDateTable) add(1, "Modèle", "(modèle)", "Aucune table marquée comme table de dates (dataCategory: Time + colonne isKey)", null);

  // portée
  let scoped = findings;
  if (opts.changed) {
    let changed = [];
    try {
      const g = (...a) => execFileSync("git", a, { cwd: opts.root, encoding: "utf8" });
      changed = [...g("diff", "--name-only", "HEAD").split("\n"), ...g("ls-files", "--others", "--exclude-standard").split("\n")]
        .filter(Boolean).map((p) => resolve(g("rev-parse", "--show-toplevel").trim(), p));
    } catch (e) { console.error("⚠  --changed : dépôt Git introuvable, analyse complète."); }
    if (changed.length) scoped = findings.filter((f) => f.file && changed.includes(resolve(f.file)));
  }
  return { findings: scoped.sort((a, b) => a.prio - b.prio || a.cat.localeCompare(b.cat)), stats: {
    tables: model.tables.size, measures: model.measures.size, columns: [...model.tables.values()].reduce((s, t) => s + t.columns.size, 0),
    relationships: model.relationships.size ?? model.relationships.length, reportRefs: report.refs.length, usedMeasures: usedM.size, usedColumns: usedC.size } };
}

// ───────────────────────── sortie ─────────────────────────
function printAudit(res, loc) {
  const P = { 1: "🔴 Priorité 1", 2: "🟠 Priorité 2", 3: "🟡 Priorité 3" };
  const s = res.stats;
  console.log(`# Audit powerbi-lean\n`);
  console.log(`Modèle : ${loc.model}\nRapport : ${loc.report || "(aucun)"}\n`);
  console.log(`${s.tables} tables · ${s.measures} mesures (${s.usedMeasures} utilisées) · ${s.columns} colonnes (${s.usedColumns} utilisées hors relations) · ${s.relationships} relations · ${s.reportRefs} références de champs dans le rapport\n`);
  if (!loc.report) console.log("> ⚠ Pas de dossier .Report : l'utilisation par le rapport n'est pas vérifiée.\n");
  console.log("> « Inutilisé » = non référencé par CE rapport. D'autres rapports connectés au modèle publié peuvent l'utiliser : vérifier avant de supprimer.\n");
  for (const p of [1, 2, 3]) {
    const f = res.findings.filter((x) => x.prio === p);
    if (!f.length) continue;
    console.log(`## ${P[p]} (${f.length})\n\n| Catégorie | Objet | Constat |\n|---|---|---|`);
    for (const x of f) console.log(`| ${x.cat} | ${x.obj.replace(/\|/g, "\\|")} | ${x.detail.replace(/\|/g, "\\|")} |`);
    console.log("");
  }
  if (!res.findings.length) console.log("Aucun constat.");
}

function printUsage(model, report, field, asJson) {
  const { usedM, usedC, why } = usage(model, report);
  const rows = [];
  if (field) {
    const m = field.match(/^(?:('(?:[^']|'')+'|[^\[]+))?\[(.+)\]$/);
    if (!m) throw new Error(`--field attendu au format Table[Nom] ou [Mesure] : ${field}`);
    const t = m[1] ? unquote(m[1].trim()) : null, n = m[2];
    const mk = "M:" + lc(n), ck = t ? "C:" + key(t, n) : null;
    const list = [...(why.get(mk) || []), ...((ck && why.get(ck)) || [])];
    const deps = [...model.measures.values()].filter((x) => daxRefs(x.expr, model)[t && model.tables.get(t)?.columns.has(n) ? "cols" : "measures"].has(t && model.tables.get(t)?.columns.has(n) ? key(t, n) : lc(n)));
    const out = { field, usedBy: [...new Set(list)], referencedByMeasures: deps.map((d) => `[${d.name}]`) };
    if (asJson) return console.log(JSON.stringify(out, null, 2));
    console.log(`# Utilisation de ${field}\n`);
    if (!out.usedBy.length && !out.referencedByMeasures.length) console.log("Aucune utilisation trouvée (rapport, DAX, relations, tri, rôles).");
    out.usedBy.forEach((u) => console.log(`- ${u}`));
    if (out.referencedByMeasures.length) console.log(`\nRéférencé dans le DAX de : ${out.referencedByMeasures.join(", ")}`);
    console.log("\nAvant un renommage : mettre à jour chacun de ces emplacements (rapport PBIR, DAX, relations, tri, rôles, cultures).");
    return;
  }
  for (const r of report.refs) rows.push({ page: r.page, visual: r.visual, field: r.kind === "Measure" ? `[${r.name}]` : key(r.table, r.name) });
  if (asJson) return console.log(JSON.stringify({ refs: rows, usedMeasures: [...usedM], usedColumns: [...usedC] }, null, 2));
  console.log(`# Champs utilisés par le rapport\n\n| Page | Visuel | Champ |\n|---|---|---|`);
  const seen = new Set();
  for (const r of rows) { const k = r.page + r.visual + r.field; if (!seen.has(k)) { seen.add(k); console.log(`| ${r.page} | ${r.visual} | ${r.field} |`); } }
}

// ───────────────────────── main ─────────────────────────
const [cmd, target, ...rest] = process.argv.slice(2);
const flag = (n) => rest.includes(n);
const val = (n) => { const i = rest.indexOf(n); return i >= 0 ? rest[i + 1] : null; };
if (!cmd || !["audit", "usage"].includes(cmd)) {
  console.log("Usage : node lean.mjs audit|usage <dossier PBIP> [--changed] [--field \"Table[Nom]\"] [--json]");
  process.exit(cmd ? 1 : 0);
}
try {
  const loc = locate(target);
  const model = loadModel(loc.model);
  const report = loadReport(loc.report, model);
  if (cmd === "audit") {
    const res = audit(model, report, { changed: flag("--changed"), root: loc.root });
    if (flag("--json")) console.log(JSON.stringify(res, null, 2)); else printAudit(res, loc);
  } else printUsage(model, report, val("--field"), flag("--json"));
} catch (e) { console.error(`✖  ${e.message}`); process.exit(1); }
