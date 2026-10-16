#!/usr/bin/env python3
"""powerbi-lean — analyse en lecture seule d'un projet PBIP (TMDL + PBIR).

Usage :
  python lean.py audit <dossier PBIP | *.SemanticModel | fichier .pbip> [--changed] [--json]
  python lean.py usage <dossier PBIP> [--field "'Table'[Nom]" | --field "[Mesure]"] [--json]
  python lean.py dette <dossier PBIP> [--json]   # état de DETTE.md + MODIFICATIONS.md

Aucun fichier n'est modifié. Python 3.8+ ; bibliothèque standard uniquement.
"""
import json
import os
import re
import subprocess
import sys
from collections import deque

if hasattr(sys.stdout, "reconfigure"):  # console Windows : forcer l'UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKIP_DIRS = {".pbi", ".git", "node_modules", "__pycache__"}


# ───────────────────────── utilitaires ─────────────────────────
def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r\n", "\n")


def walk(root, pred):
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = os.path.join(dirpath, name)
            if pred(p):
                out.append(p)
    return sorted(out)


def unquote(s):
    if s and len(s) >= 2 and s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("''", "'")
    return s


def key(table, name):
    return f"{table}[{name}]"


def is_simple_name(name):
    return re.fullmatch(r"[A-Za-z_]\w*", name) is not None


# ───────────────────────── localisation ─────────────────────────
def locate(arg):
    p = os.path.abspath(arg or ".")
    sm = None
    if p.endswith(".SemanticModel"):
        sm = p
    elif p.endswith(".pbip"):
        p = os.path.dirname(p)
    if not sm:
        cands = sorted(d for d in os.listdir(p) if d.endswith(".SemanticModel"))
        if not cands:
            raise SystemExit(f"✖  Aucun dossier *.SemanticModel dans {p}")
        sm = os.path.join(p, cands[0])
    parent = os.path.dirname(sm)
    prefix = os.path.basename(sm)[: -len(".SemanticModel")]
    reports = sorted(d for d in os.listdir(parent) if d.endswith(".Report"))
    rep = f"{prefix}.Report" if f"{prefix}.Report" in reports else (reports[0] if reports else None)
    return {
        "root": parent,
        "model": os.path.join(sm, "definition"),
        "report": os.path.join(parent, rep, "definition") if rep else None,
    }


# ───────────────────────── parseur TMDL ─────────────────────────
NAME = r"'(?:[^']|'')+'|[^\s=:'][^=:]*?"
OBJ = re.compile(rf"^([A-Za-z]+)\s+({NAME})\s*(?:=\s*(.*))?$")
PROP_EXPR = re.compile(r"^([A-Za-z]+)\s*=\s*(.*)$")
PROP = re.compile(r"^([A-Za-z]+)\s*:\s*(.*)$")
BARE = re.compile(r"^([A-Za-z]+)$")
QUOTED = re.compile(r"'(?:[^']|'')+'")
OBJECT_KINDS = {
    "table", "column", "measure", "partition", "hierarchy", "level", "calculationGroup",
    "calculationItem", "role", "tablePermission", "relationship", "expression", "annotation",
    "extendedProperty", "perspective", "culture", "model", "database", "ref", "dataSource",
    "linguisticMetadata", "columnPermission",
}


def indent_of(line):
    return len(line) - len(line.lstrip("\t"))


def parse_tmdl(text):
    lines = text.split("\n")
    root = {"kind": "root", "children": [], "level": -1, "props": {}}
    stack = [root]
    desc = []
    i = 0
    n = len(lines)

    def collect(first, lvl):
        nonlocal i
        buf = []
        if first == "```":
            i += 1
            while i < n and lines[i].strip() != "```":
                buf.append(lines[i])
                i += 1
            return "\n".join(buf)
        if first:
            buf.append(first)
        while i + 1 < n:
            nxt = lines[i + 1]
            if nxt.strip() == "":
                buf.append("")
                i += 1
                continue
            if indent_of(nxt) >= lvl + 2:
                buf.append(nxt)
                i += 1
            else:
                break
        return "\n".join(buf).strip()

    while i < n:
        raw = lines[i]
        t = raw.strip()
        if not t:
            i += 1
            continue
        lvl = indent_of(raw)
        if t.startswith("///"):
            desc.append(t[3:].strip())
            i += 1
            continue
        while len(stack) > 1 and stack[-1]["level"] >= lvl:
            stack.pop()
        parent = stack[-1]
        m = OBJ.match(t)
        if m and m.group(1) in OBJECT_KINDS and not PROP.match(QUOTED.sub("x", t)):
            node = {"kind": m.group(1), "name": unquote(m.group(2).strip()), "level": lvl,
                    "props": {}, "children": [], "desc": "\n".join(desc)}
            if m.group(3) is not None:
                node["expr"] = collect(m.group(3).strip(), lvl)
            parent["children"].append(node)
            stack.append(node)
            desc = []
            i += 1
            continue
        desc = []
        m = PROP_EXPR.match(t)
        if m and ":" not in t:
            parent["props"][m.group(1)] = collect(m.group(2).strip(), lvl)
        elif PROP.match(t):
            m = PROP.match(t)
            parent["props"][m.group(1)] = m.group(2).strip()
        elif BARE.match(t):
            word = BARE.match(t).group(1)
            if word in OBJECT_KINDS:
                node = {"kind": word, "name": "", "level": lvl, "props": {}, "children": []}
                parent["children"].append(node)
                stack.append(node)
            else:
                parent["props"][word] = True
        elif m:
            parent["props"][m.group(1)] = collect(m.group(2).strip(), lvl)
        i += 1
    return root


def split_col_ref(s):
    m = re.match(r"^('(?:[^']|'')+'|[^.]+)\.(.+)$", s or "")
    return (unquote(m.group(1)), unquote(m.group(2))) if m else (None, None)


def load_model(model_dir):
    model = {"tables": {}, "measures": {}, "relationships": [], "roles": []}
    for f in walk(model_dir, lambda p: p.endswith(".tmdl")):
        tree = parse_tmdl(read(f))
        for nd in tree["children"]:
            if nd["kind"] == "table":
                tb = {"name": nd["name"], "desc": nd.get("desc", ""), "props": nd["props"], "file": f,
                      "columns": {}, "measures": {}, "hierarchies": [], "partitions": [], "calc_group": None}
                for c in nd["children"]:
                    if c["kind"] == "column":
                        tb["columns"][c["name"]] = {"name": c["name"], "expr": c.get("expr"),
                                                    "props": c["props"], "desc": c.get("desc", "")}
                    elif c["kind"] == "measure":
                        ms = {"name": c["name"], "table": nd["name"], "expr": c.get("expr", ""),
                              "props": c["props"], "desc": c.get("desc", ""), "file": f}
                        tb["measures"][c["name"]] = ms
                        model["measures"][c["name"].lower()] = ms
                    elif c["kind"] == "hierarchy":
                        tb["hierarchies"].append({"name": c["name"], "levels": [
                            {"name": l["name"], "column": unquote(l["props"].get("column"))}
                            for l in c["children"] if l["kind"] == "level"]})
                    elif c["kind"] == "partition":
                        tb["partitions"].append({"name": c["name"], "type": (c.get("expr") or "").strip(),
                                                 "source": c["props"].get("source", "")})
                    elif c["kind"] == "calculationGroup":
                        tb["calc_group"] = [{"name": x["name"], "expr": x.get("expr", "")}
                                            for x in c["children"] if x["kind"] == "calculationItem"]
                model["tables"][nd["name"]] = tb
            elif nd["kind"] == "relationship":
                model["relationships"].append({"name": nd["name"], "props": nd["props"], "file": f,
                                               "from": split_col_ref(nd["props"].get("fromColumn")),
                                               "to": split_col_ref(nd["props"].get("toColumn"))})
            elif nd["kind"] == "role":
                model["roles"].append({"name": nd["name"], "file": f, "perms": [
                    {"table": c["name"], "expr": c.get("expr", "")}
                    for c in nd["children"] if c["kind"] == "tablePermission"]})
    return model


# ───────────────────────── DAX ─────────────────────────
def strip_dax(expr, keep_strings=False):
    """Retire les commentaires (// -- /* */) ; remplace les chaînes par "" sauf keep_strings."""
    out, i, n = [], 0, len(expr or "")
    expr = expr or ""
    while i < n:
        c = expr[i]
        nx = expr[i + 1] if i + 1 < n else ""
        if c in ('"', "'"):
            j = i + 1
            while j < n:
                if expr[j] == c and j + 1 < n and expr[j + 1] == c:
                    j += 2
                elif expr[j] == c:
                    break
                else:
                    j += 1
            if c == '"' and not keep_strings:
                out.append('""')
            else:
                out.append(expr[i:j + 1])
            i = j + 1
            continue
        if c == "[":
            j = expr.find("]", i)
            j = n - 1 if j < 0 else j
            out.append(expr[i:j + 1])
            i = j + 1
            continue
        if (c == "/" and nx == "/") or (c == "-" and nx == "-"):
            j = expr.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "/" and nx == "*":
            j = expr.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


TBL = r"'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_]*"
QUALIFIED = re.compile(rf"({TBL})\s*\[([^\]]+)\]")


def table_pattern(tn):
    quoted = "'" + re.escape(tn.replace("'", "''")) + "'"
    return quoted + ("|" + re.escape(tn) if is_simple_name(tn) else "")


def dax_refs(expr, model):
    code = strip_dax(expr or "")
    cols, measures, tables = set(), set(), set()

    def on_qualified(m):
        tn, name = unquote(m.group(1)), m.group(2)
        tb = model["tables"].get(tn)
        if tb:
            tables.add(tn)
            if name in tb["columns"]:
                cols.add(key(tn, name))
            elif name.lower() in model["measures"]:
                measures.add(name.lower())
        return " "

    rest = QUALIFIED.sub(on_qualified, code)
    for m in re.finditer(r"\[([^\]]+)\]", rest):
        if m.group(1).lower() in model["measures"]:
            measures.add(m.group(1).lower())
    for tn in model["tables"]:
        if re.search(rf"(^|[^\w'])({table_pattern(tn)})(?![\w\[])", rest):
            tables.add(tn)
    return {"cols": cols, "measures": measures, "tables": tables, "code": code}


# ───────────────────────── PBIR ─────────────────────────
def load_report(report_dir, model):
    refs, pages = [], {}
    if not report_dir:
        return {"refs": refs, "pages": pages}
    for f in walk(os.path.join(report_dir, "pages"), lambda p: os.path.basename(p) == "page.json"):
        try:
            j = json.loads(read(f))
            folder = os.path.basename(os.path.dirname(f))
            pages[folder] = j.get("displayName") or folder
        except (ValueError, OSError):
            pass
    for f in walk(report_dir, lambda p: p.endswith(".json")):
        try:
            j = json.loads(read(f))
        except (ValueError, OSError):
            continue
        rel = os.path.relpath(f, report_dir).split(os.sep)
        page = "(rapport)"
        if "pages" in rel:
            pi = rel.index("pages")
            if pi + 1 < len(rel) and rel[pi + 1] != "pages.json":
                page = pages.get(rel[pi + 1], rel[pi + 1])
        if "visuals" in rel:
            vi = rel.index("visuals")
            vtype = (j.get("visual") or {}).get("visualType", "visuel") if isinstance(j, dict) else "visuel"
            visual = f"{vtype} {rel[vi + 1]}"
        else:
            visual = os.path.basename(f)

        def entity(expr, aliases):
            sr = (expr or {}).get("SourceRef") or {}
            return sr.get("Entity") or aliases.get(sr.get("Source"))

        def visit(node, aliases):
            if isinstance(node, list):
                for x in node:
                    visit(x, aliases)
                return
            if not isinstance(node, dict):
                return
            al = aliases
            if isinstance(node.get("From"), list):
                al = dict(aliases)
                for fr in node["From"]:
                    if isinstance(fr, dict) and fr.get("Name") and fr.get("Entity"):
                        al[fr["Name"]] = fr["Entity"]
            for kind in ("Measure", "Column"):
                v = node.get(kind)
                if isinstance(v, dict) and v.get("Property") and v.get("Expression"):
                    t = entity(v["Expression"], al)
                    if t:
                        refs.append({"table": t, "name": v["Property"], "kind": kind,
                                     "page": page, "visual": visual, "file": f})
            hl = node.get("HierarchyLevel")
            if isinstance(hl, dict) and isinstance((hl.get("Expression") or {}).get("Hierarchy"), dict):
                h = hl["Expression"]["Hierarchy"]
                t = entity(h.get("Expression"), al)
                if t:
                    col = hl.get("Level")
                    tb = model["tables"].get(t)
                    if tb:
                        for hh in tb["hierarchies"]:
                            if hh["name"] == h.get("Hierarchy"):
                                for lv in hh["levels"]:
                                    if lv["name"] == hl.get("Level") and lv["column"]:
                                        col = lv["column"]
                    refs.append({"table": t, "name": col, "kind": "Column",
                                 "page": page, "visual": visual, "file": f})
            for v in node.values():
                visit(v, al)

        visit(j, {})
    return {"refs": refs, "pages": pages}


# ───────────────────────── graphe d'utilisation ─────────────────────────
def compute_usage(model, report):
    used_m, used_c, why = set(), set(), {}
    queue = deque()

    def note(k, reason):
        why.setdefault(k, []).append(reason)

    def use_m(name, reason):
        k = name.lower()
        if k not in model["measures"]:
            return
        note("M:" + k, reason)
        if k not in used_m:
            used_m.add(k)
            queue.append(("M", k))

    def use_c(t, name, reason):
        tb = model["tables"].get(t)
        if not tb or name not in tb["columns"]:
            return
        k = key(t, name)
        note("C:" + k, reason)
        if k not in used_c:
            used_c.add(k)
            queue.append(("C", (t, name)))

    def from_dax(expr, reason):
        d = dax_refs(expr, model)
        for m in sorted(d["measures"]):
            use_m(model["measures"][m]["name"], reason)
        for c in sorted(d["cols"]):
            t, name = re.match(r"^(.*)\[(.*)\]$", c).groups()
            use_c(t, name, reason)

    for r in report["refs"]:
        label = f"rapport : {r['page']} / {r['visual']}"
        if r["kind"] == "Measure":
            use_m(r["name"], label)
        else:
            use_c(r["table"], r["name"], label)
    for rel in model["relationships"]:
        for t, c in (rel["from"], rel["to"]):
            if t:
                use_c(t, c, "relation")
    for ro in model["roles"]:
        for p in ro["perms"]:
            from_dax(p["expr"], f"rôle {ro['name']}")
    for tb in model["tables"].values():
        for p in tb["partitions"]:
            if p["type"].lower().startswith("calculated"):
                from_dax(p["source"], f"table calculée {tb['name']}")
        for ci in tb["calc_group"] or []:
            from_dax(ci["expr"], f"groupe de calcul {tb['name']}")
        if tb["props"].get("dataCategory") == "Time":
            for c in tb["columns"].values():
                if c["props"].get("isKey"):
                    use_c(tb["name"], c["name"], "clé de la table de dates")
    while queue:
        kind, k = queue.popleft()
        if kind == "M":
            m = model["measures"][k]
            from_dax(m["expr"], f"mesure [{m['name']}]")
            if m["props"].get("formatStringDefinition"):
                from_dax(m["props"]["formatStringDefinition"], f"format de [{m['name']}]")
        else:
            t, name = k
            c = model["tables"][t]["columns"][name]
            if c.get("expr"):
                from_dax(c["expr"], f"colonne calculée {key(t, name)}")
            if c["props"].get("sortByColumn"):
                use_c(t, unquote(c["props"]["sortByColumn"]), f"tri de {key(t, name)}")
    return used_m, used_c, why


# ───────────────────────── audit ─────────────────────────
RULES = [
    ("dateDure", re.compile(r"\bDATE\s*\(\s*\d{4}\s*,", re.I), "Date codée en dur (DATE(aaaa, …))", 3),
    ("dateSysteme", re.compile(r"\b(TODAY|NOW|UTCTODAY|UTCNOW)\s*\(\s*\)", re.I),
     "Date système (TODAY/NOW) : résultat non reproductible", 2),
    ("iferror", re.compile(r"\b(IFERROR|ISERROR)\s*\(", re.I), "IFERROR / ISERROR", 2),
    ("division", re.compile(r"[\w\])]\s*/\s*[A-Za-z_(\[']"),
     "Division « / » par une expression au lieu de DIVIDE", 3),
]
COL_CMP = re.compile(rf"({TBL})\s*\[([^\]]+)\]\s*(=|<>|IN)\s*(\{{[^}}]*\}}|\"[^\"]*\"|-?\d+)", re.I)
ID_LIKE = re.compile(r"(^|[\s_])(id|key|cle|clé|code|annee|année|year|mois|month|trimestre|quarter|num|no|"
                     r"numero|numéro)([\s_]|$)|(id|key)$", re.I)


def audit(model, report, changed=False, root=None):
    used_m, used_c, _ = compute_usage(model, report)
    findings = []

    def add(prio, cat, obj, detail, file):
        findings.append({"prio": prio, "cat": cat, "obj": obj, "detail": detail, "file": file})

    rel_tables = {t for r in model["relationships"] for t in (r["from"][0], r["to"][0]) if t}
    by_norm = {}
    for m in model["measures"].values():
        obj = f"[{m['name']}] ({m['table']})"
        code = strip_dax(m["expr"])
        with_str = strip_dax(m["expr"], keep_strings=True)
        hidden = bool(m["props"].get("isHidden"))
        if m["name"].lower() not in used_m:
            add(2, "Inutilisée", obj,
                f"Mesure{' masquée' if hidden else ''} jamais utilisée par le rapport ni par une autre mesure", m["file"])
        for _, rx, label, prio in RULES:
            mm = rx.search(code)
            if mm:
                add(prio, "Valeur en dur / risque", obj, f"{label} — « {mm.group(0).strip()} »", m["file"])
        for mm in COL_CMP.finditer(with_str):
            tn, lit = unquote(mm.group(1)), mm.group(4)
            if tn not in model["tables"] or tn not in rel_tables or re.fullmatch(r"-?\d", lit):
                continue
            kind = "Libellé" if lit.startswith('"') else ("Liste de valeurs" if lit.startswith("{") else "Valeur numérique")
            add(3, "Valeur en dur / risque", obj,
                f"{kind} en dur comparé(e) à {tn}[{mm.group(2)}] — « {mm.group(0)[:80]} » : "
                "passer par une mesure ou une table de référence", m["file"])
        for tn in model["tables"]:
            if re.search(rf"\bFILTER\s*\(\s*({table_pattern(tn)})\s*,", code, re.I):
                add(2, "DAX", obj, f"FILTER sur la table entière {tn} : préférer un filtre de colonne "
                                   "ou VALUES/ALL sur la colonne", m["file"])
        if not hidden and not m["desc"]:
            add(3, "Documentation", obj, "Mesure visible sans description", m["file"])
        if (not hidden and not m["props"].get("formatString") and not m["props"].get("formatStringDefinition")
                and '""' not in code):
            add(3, "Documentation", obj, "Mesure visible sans format", m["file"])
        norm = re.sub(r"\s+", "", with_str.lower())
        if len(norm) > 12:
            by_norm.setdefault(norm, []).append(m)
    for grp in by_norm.values():
        if len(grp) > 1:
            add(1, "Doublon", ", ".join(f"[{m['name']}]" for m in grp),
                "Expressions DAX identiques (hors commentaires et espaces) : garder une mesure, "
                "faire référencer les autres", grp[0]["file"])

    rel_cols = {key(*r[side]) for r in model["relationships"] for side in ("from", "to") if r[side][0]}
    fk_cols = {key(*r["from"]) for r in model["relationships"] if r["from"][0]}
    has_date_table = False
    for tb in model["tables"].values():
        if tb["props"].get("dataCategory") == "Time":
            has_date_table = True
        is_measure_table = bool(tb["measures"]) and all(c["props"].get("isHidden") for c in tb["columns"].values())
        if tb["name"] not in rel_tables and not tb["calc_group"] and not is_measure_table:
            add(3, "Structure", tb["name"],
                "Table sans relation (normal pour un paramètre / une table déconnectée ; sinon à vérifier)", tb["file"])
        for c in tb["columns"].values():
            k = key(tb["name"], c["name"])
            if k not in used_c and k not in rel_cols and not is_measure_table:
                add(2, "Inutilisée", k, f"Colonne{' masquée' if c['props'].get('isHidden') else ''} jamais utilisée "
                                        "(rapport, DAX, relations, tri) : candidate à la suppression", tb["file"])
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", c["name"])
            if str(c["props"].get("summarizeBy", "")).lower() == "sum" and ID_LIKE.search(spaced):
                add(2, "Modèle", k, "summarizeBy: sum sur une colonne qui ressemble à un identifiant / une année : "
                                    "mettre none", tb["file"])
            if k in fk_cols and not c["props"].get("isHidden"):
                add(3, "Modèle", k, "Clé étrangère visible : la masquer", tb["file"])
    if not has_date_table:
        add(1, "Modèle", "(modèle)", "Aucune table marquée comme table de dates (dataCategory: Time + colonne isKey)", None)

    if changed:
        try:
            def git(*a):
                return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, check=True).stdout
            top = git("rev-parse", "--show-toplevel").strip()
            files = git("diff", "--name-only", "HEAD").splitlines() + \
                git("ls-files", "--others", "--exclude-standard").splitlines()
            changed_set = {os.path.normcase(os.path.abspath(os.path.join(top, p))) for p in files if p}
            findings = [f for f in findings if f["file"] and os.path.normcase(os.path.abspath(f["file"])) in changed_set]
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠  --changed : dépôt Git introuvable, analyse complète.", file=sys.stderr)

    findings.sort(key=lambda f: (f["prio"], f["cat"]))
    stats = {
        "tables": len(model["tables"]), "measures": len(model["measures"]),
        "columns": sum(len(t["columns"]) for t in model["tables"].values()),
        "relationships": len(model["relationships"]), "reportRefs": len(report["refs"]),
        "usedMeasures": len(used_m), "usedColumns": len(used_c),
    }
    return {"findings": findings, "stats": stats}


# ───────────────────────── sortie ─────────────────────────
def esc(s):
    return str(s).replace("|", "\\|")


def print_audit(res, loc):
    s = res["stats"]
    print("# Audit powerbi-lean\n")
    print(f"Modèle : {loc['model']}\nRapport : {loc['report'] or '(aucun)'}\n")
    print(f"{s['tables']} tables · {s['measures']} mesures ({s['usedMeasures']} utilisées) · {s['columns']} colonnes "
          f"({s['usedColumns']} utilisées hors relations) · {s['relationships']} relations · "
          f"{s['reportRefs']} références de champs dans le rapport\n")
    if not loc["report"]:
        print("> ⚠ Pas de dossier .Report : l'utilisation par le rapport n'est pas vérifiée.\n")
    print("> « Inutilisé » = non référencé par CE rapport. D'autres rapports connectés au modèle publié "
          "peuvent l'utiliser : vérifier avant de supprimer.\n")
    for p in (1, 2, 3):
        rows = [f for f in res["findings"] if f["prio"] == p]
        if not rows:
            continue
        print(f"## Priorité {p} ({len(rows)})\n\n| Catégorie | Objet | Constat |\n|---|---|---|")
        for f in rows:
            print(f"| {f['cat']} | {esc(f['obj'])} | {esc(f['detail'])} |")
        print()
    if not res["findings"]:
        print("Aucun constat.")


def print_usage(model, report, field, as_json):
    used_m, used_c, why = compute_usage(model, report)
    if field:
        m = re.match(r"^(?:('(?:[^']|'')+'|[^\[]+))?\[(.+)\]$", field)
        if not m:
            raise SystemExit(f"✖  --field attendu au format Table[Nom] ou [Mesure] : {field}")
        t = unquote(m.group(1).strip()) if m.group(1) else None
        name = m.group(2)
        is_col = bool(t and model["tables"].get(t) and name in model["tables"][t]["columns"])
        used_by = list(dict.fromkeys(why.get("M:" + name.lower(), []) + (why.get("C:" + key(t, name), []) if t else [])))
        target = key(t, name) if is_col else name.lower()
        deps = [f"[{x['name']}]" for x in model["measures"].values()
                if target in dax_refs(x["expr"], model)["cols" if is_col else "measures"]]
        out = {"field": field, "usedBy": used_by, "referencedByMeasures": deps}
        if as_json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return
        print(f"# Utilisation de {field}\n")
        if not used_by and not deps:
            print("Aucune utilisation trouvée (rapport, DAX, relations, tri, rôles).")
        for u in used_by:
            print(f"- {u}")
        if deps:
            print(f"\nRéférencé dans le DAX de : {', '.join(deps)}")
        print("\nAvant un renommage : mettre à jour chacun de ces emplacements "
              "(rapport PBIR, DAX, relations, tri, rôles, cultures).")
        return
    rows = [{"page": r["page"], "visual": r["visual"],
             "field": f"[{r['name']}]" if r["kind"] == "Measure" else key(r["table"], r["name"])}
            for r in report["refs"]]
    if as_json:
        print(json.dumps({"refs": rows, "usedMeasures": sorted(used_m), "usedColumns": sorted(used_c)},
                         ensure_ascii=False, indent=2))
        return
    print("# Champs utilisés par le rapport\n\n| Page | Visuel | Champ |\n|---|---|---|")
    seen = set()
    for r in rows:
        k = (r["page"], r["visual"], r["field"])
        if k not in seen:
            seen.add(k)
            print(f"| {esc(r['page'])} | {esc(r['visual'])} | {esc(r['field'])} |")



# ───────────────────────── dette & journal ─────────────────────────
DEBT_ID = re.compile(r"\bD-\d{3,}\b")
MOD_ID = re.compile(r"\bM-\d{3,}\b")
DEBT_REF = re.compile(r"\b(D-\d{3,})\b(?:\s*\((partielle?|en cours)\))?", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def field(body, name):
    m = re.search(rf"\*\*{name}\*\*\s*:\s*([^\n·]+)", body, re.I)
    return m.group(1).strip() if m else ""


def parse_debt(path):
    """DETTE.md : sections « ## Ouvert » / « ## Soldé », entrées « ### D-001 · titre »."""
    items, section = [], None
    if not os.path.isfile(path):
        return items
    text = read(path)
    for block in re.split(r"(?m)^(?=#{2,3} )", text):
        head = block.split("\n", 1)[0]
        if head.startswith("## "):
            low = head.lower()
            section = "solde" if "sold" in low else ("ouvert" if "ouvert" in low else section)
            continue
        m = re.match(r"^### (D-\d{3,})\s*[·\-:]\s*(.*)$", head)
        if not m:
            continue
        body = block.split("\n", 1)[1] if "\n" in block else ""
        items.append({
            "id": m.group(1), "title": m.group(2).strip(), "status": section or "ouvert",
            "priority": field(body, "Priorité").lower() or "non précisée",
            "due": (DATE.search(field(body, "Échéance")) or [None])[0] if field(body, "Échéance") else None,
            "closed": (DATE.search(field(body, "Soldé le")) or [None])[0] if field(body, "Soldé le") else None,
            "mods": MOD_ID.findall(field(body, "Modification")),
        })
    return items


def parse_mods(path):
    """MODIFICATIONS.md : entrées « ## M-001 · 2026-10-20 · titre » (plus récentes en haut)."""
    mods = []
    if not os.path.isfile(path):
        return mods
    for block in re.split(r"(?m)^(?=## )", read(path)):
        head = block.split("\n", 1)[0]
        m = re.match(r"^## (M-\d{3,})\s*[·\-:]\s*(.*)$", head)
        if not m:
            continue
        body = block.split("\n", 1)[1] if "\n" in block else ""
        d = DATE.search(m.group(2))
        mods.append({"id": m.group(1), "date": d.group(0) if d else None,
                     "title": DATE.sub("", m.group(2)).strip(" ·-:"),
                     "debts": [d for d, mark in DEBT_REF.findall(field(body, "Dette")) if not mark],
                     "partial": [d for d, mark in DEBT_REF.findall(field(body, "Dette")) if mark],
                     "type": field(body, "Type")})
    return mods


def debt_report(root, today=None):
    import datetime
    today = today or datetime.date.today().isoformat()
    debts = parse_debt(os.path.join(root, "DETTE.md"))
    mods = parse_mods(os.path.join(root, "MODIFICATIONS.md"))
    by_id = {d["id"]: d for d in debts}
    open_ = [d for d in debts if d["status"] == "ouvert"]
    closed = [d for d in debts if d["status"] == "solde"]
    mod_ids = {m["id"] for m in mods}
    debts_in_mods = {x for m in mods for x in m["debts"]}
    issues = []
    for d in open_:
        if d["due"] and d["due"] < today:
            issues.append(f"{d['id']} : échéance dépassée ({d['due']})")
        if d["id"] in debts_in_mods:
            issues.append(f"{d['id']} : citée dans MODIFICATIONS.md mais encore « Ouvert » dans DETTE.md")
    for d in closed:
        if not d["mods"] and d["id"] not in debts_in_mods:
            issues.append(f"{d['id']} : soldée sans modification liée dans MODIFICATIONS.md")
        for mid in d["mods"]:
            if mid not in mod_ids:
                issues.append(f"{d['id']} : renvoie à {mid}, absente de MODIFICATIONS.md")
    for m in mods:
        for did in m["debts"] + m["partial"]:
            if did not in by_id:
                issues.append(f"{m['id']} : cite {did}, absente de DETTE.md")
    ids = [int(m["id"][2:]) for m in mods]
    if len(ids) != len(set(ids)):
        issues.append("MODIFICATIONS.md : identifiants M-xxx en double")
    prio = {}
    for d in open_:
        prio[d["priority"]] = prio.get(d["priority"], 0) + 1
    total = len(debts)
    return {
        "today": today, "total": total, "open": len(open_), "closed": len(closed),
        "progress": round(100 * len(closed) / total) if total else None,
        "openByPriority": prio, "modifications": len(mods),
        "lastModification": mods[0] if mods else None,
        "nextId": {"dette": f"D-{max([int(d['id'][2:]) for d in debts] or [0]) + 1:03d}",
                   "modification": f"M-{max(ids or [0]) + 1:03d}"},
        "openItems": [{k: d[k] for k in ("id", "title", "priority", "due")} for d in open_],
        "issues": issues,
    }


def print_debt(rep, root):
    print("# Dette et modifications\n")
    print(f"Projet : {root}\n")
    if not rep["total"] and not rep["modifications"]:
        print("Ni DETTE.md ni MODIFICATIONS.md trouvés à la racine du projet.")
        return
    bar = ""
    if rep["progress"] is not None:
        filled = rep["progress"] // 5
        bar = "█" * filled + "░" * (20 - filled)
    print(f"| Dette | Valeur |\n|---|---|")
    print(f"| Entrées | {rep['total']} |\n| Ouvertes | {rep['open']} |\n| Soldées | {rep['closed']} |")
    if rep["progress"] is not None:
        print(f"| Progression | {bar} {rep['progress']} % |")
    print(f"| Modifications journalisées | {rep['modifications']} |\n")
    if rep["openByPriority"]:
        print("Ouvertes par priorité : " + ", ".join(f"{k} {v}" for k, v in sorted(rep["openByPriority"].items())) + "\n")
    if rep["lastModification"]:
        lm = rep["lastModification"]
        print(f"Dernière modification : {lm['id']} · {lm['date'] or '?'} · {lm['title']}\n")
    print(f"Prochains identifiants : {rep['nextId']['dette']} (dette), {rep['nextId']['modification']} (modification)\n")
    if rep["issues"]:
        print("## Incohérences\n")
        for i in rep["issues"]:
            print(f"- {i}")
    else:
        print("Aucune incohérence entre DETTE.md et MODIFICATIONS.md.")


# ───────────────────────── main ─────────────────────────
def main(argv):
    if not argv or argv[0] not in ("audit", "usage", "dette"):
        print('Usage : python lean.py audit|usage|dette <dossier PBIP> [--changed] [--field "Table[Nom]"] [--json]')
        return 0 if not argv else 1
    cmd, rest = argv[0], argv[1:]
    target = rest[0] if rest and not rest[0].startswith("--") else "."
    if cmd == "dette":
        root = os.path.dirname(os.path.abspath(target)) if target.endswith(".pbip") else os.path.abspath(target)
        if root.endswith((".SemanticModel", ".Report")):
            root = os.path.dirname(root)
        rep = debt_report(root)
        if "--json" in rest:
            print(json.dumps(rep, ensure_ascii=False, indent=2))
        else:
            print_debt(rep, root)
        return 0
    field = rest[rest.index("--field") + 1] if "--field" in rest and rest.index("--field") + 1 < len(rest) else None
    loc = locate(target)
    model = load_model(loc["model"])
    report = load_report(loc["report"], model)
    if cmd == "audit":
        res = audit(model, report, changed="--changed" in rest, root=loc["root"])
        if "--json" in rest:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print_audit(res, loc)
    else:
        print_usage(model, report, field, "--json" in rest)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"✖  {exc}", file=sys.stderr)
        sys.exit(1)
