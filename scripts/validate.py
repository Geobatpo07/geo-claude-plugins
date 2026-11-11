#!/usr/bin/env python3
"""Contrôle de cohérence du dépôt — usage : python scripts/validate.py"""
import json
import os
import re
import sys

from common import ROOT, parse_frontmatter, read_text, utf8_console

utf8_console()
# Skills et serveurs tiers (Microsoft) que nos skills peuvent citer sans les contenir.
EXTERNAL = {"powerbi-report-cli", "powerbi-authoring", "powerbi-modeling-mcp"}
# Marqueurs propres à un seul agent : les skills doivent rester lisibles par tous (Codex, Grok, Gemini…).
AGENT_SPECIFIC = re.compile(r"CLAUDE_PLUGIN_ROOT|~/\.claude|\b(?:Claude|Codex|Grok|Gemini|Copilot|Cursor)\b")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
errors, warnings = [], []


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        errors.append(f"{path} : JSON invalide ({exc})")
        return None


def check_agents(folder, label, known=None):
    """Sous-agents (*.md) : frontmatter name = nom du fichier, description ; skills cités existants."""
    names = []
    for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not f.endswith(".md"):
            continue
        text = read_text(os.path.join(folder, f))
        fm = parse_frontmatter(text)
        alabel = f"{label} : sous-agent {f}"
        if fm is None:
            errors.append(f"{alabel} sans frontmatter")
            continue
        if fm.get("name") != f[:-3] or not KEBAB.match(f[:-3]):
            errors.append(f"{alabel} : name \"{fm.get('name')}\" ≠ nom du fichier (kebab-case)")
        if not fm.get("description"):
            errors.append(f"{alabel} : description manquante")
        names.append((f[:-3], alabel, text))
    if known is not None:
        known = known | {n for n, _, _ in names}
        for _, alabel, text in names:
            for ref in sorted(set(re.findall(r"`(powerbi-[a-z0-9-]+)`", text)) - known - EXTERNAL):
                errors.append(f"{alabel} : skill cité inconnu `{ref}`")
    return {n for n, _, _ in names}


def main():
    market = read_json(os.path.join(ROOT, ".claude-plugin", "marketplace.json"))
    if market:
        if not KEBAB.match(market.get("name") or ""):
            errors.append(f"marketplace.json : nom \"{market.get('name')}\" non kebab-case")
        seen = set()
        for p in market.get("plugins", []):
            label = f"plugin \"{p.get('name')}\""
            if p.get("name") in seen:
                errors.append(f"{label} : déclaré deux fois")
            seen.add(p.get("name"))
            if not KEBAB.match(p.get("name") or ""):
                errors.append(f"{label} : nom non kebab-case")
            if not SEMVER.match(p.get("version") or ""):
                errors.append(f"{label} : version \"{p.get('version')}\" non SemVer")
            pdir = os.path.normpath(os.path.join(ROOT, p.get("source") or ""))
            if not os.path.isdir(pdir):
                errors.append(f"{label} : source introuvable ({p.get('source')})")
                continue
            manifest = read_json(os.path.join(pdir, ".claude-plugin", "plugin.json"))
            if manifest:
                if manifest.get("name") != p.get("name"):
                    errors.append(f"{label} : plugin.json name = \"{manifest.get('name')}\"")
                if manifest.get("version") != p.get("version"):
                    errors.append(f"{label} : version marketplace ({p.get('version')}) ≠ plugin.json "
                                  f"({manifest.get('version')})")
            docs_cmds = [os.path.join(pdir, "commands", f) for f in sorted(os.listdir(os.path.join(pdir, "commands")))
                         if f.endswith("-docs.md")] if os.path.isdir(os.path.join(pdir, "commands")) else []
            docs_text = "".join(open(f, encoding="utf-8-sig").read() for f in docs_cmds)
            if os.path.isdir(os.path.join(pdir, "commands")):
                for cf in sorted(os.listdir(os.path.join(pdir, "commands"))):
                    if cf.endswith(".md") and parse_frontmatter(open(os.path.join(pdir, "commands", cf),
                                                                      encoding="utf-8-sig").read()) is None:
                        errors.append(f"{label} : commande {cf} sans frontmatter (description)")
            skills_dir = os.path.join(pdir, "skills")
            if not os.path.isdir(skills_dir):
                warnings.append(f"{label} : aucun dossier skills/")
                continue
            known = {s for s in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, s))}
            known |= check_agents(os.path.join(pdir, "agents"), label, known)
            for s in sorted(os.listdir(skills_dir)):
                sdir = os.path.join(skills_dir, s)
                if not os.path.isdir(sdir):
                    continue
                slabel = f"skill \"{p.get('name')}/{s}\""
                skill_file = os.path.join(sdir, "SKILL.md")
                if not os.path.isfile(skill_file):
                    errors.append(f"{slabel} : SKILL.md manquant")
                    continue
                with open(skill_file, encoding="utf-8-sig") as f:
                    text = f.read()
                fm = parse_frontmatter(text)
                if fm is None:
                    errors.append(f"{slabel} : frontmatter manquant")
                    continue
                name = fm.get("name") or ""
                if name != s:
                    errors.append(f"{slabel} : name \"{name}\" ≠ nom du dossier")
                if not KEBAB.match(name) or len(name) > 64:
                    errors.append(f"{slabel} : name invalide")
                desc = fm.get("description")
                if not desc:
                    errors.append(f"{slabel} : description manquante")
                elif len(desc) > 1024:
                    errors.append(f"{slabel} : description > 1024 caractères")
                lines = len(text.splitlines())
                if lines > 300:
                    warnings.append(f"{slabel} : {lines} lignes (> 300, déplacer vers references/)")
                if docs_cmds and f"`{s}`" not in docs_text:
                    errors.append(f"{slabel} : absent de la commande de documentation ({os.path.basename(docs_cmds[0])})")
                for dirpath, _, filenames in os.walk(sdir):
                    for fn in sorted(filenames):
                        if not fn.endswith(".md"):
                            continue
                        fpath = os.path.join(dirpath, fn)
                        rel = os.path.relpath(fpath, sdir).replace(os.sep, "/")
                        ftext = read_text(fpath)
                        for ref in re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)", ftext):
                            if "[" in ref or "<" in ref:  # espace réservé d'un modèle
                                continue
                            dest = os.path.normpath(os.path.join(dirpath, ref))
                            if not dest.startswith(os.path.normpath(pdir) + os.sep):
                                errors.append(f"{slabel} : {rel} référence un fichier hors du plugin ({ref})")
                            elif not os.path.exists(dest):
                                errors.append(f"{slabel} : lien cassé {ref} (dans {rel})")
                        for ref in sorted(set(re.findall(r"`(powerbi-[a-z0-9-]+)`", ftext)) - known - EXTERNAL):
                            errors.append(f"{slabel} : {rel} cite un skill inconnu `{ref}`")
                        hit = AGENT_SPECIFIC.search(ftext)
                        if hit and rel == "SKILL.md":
                            warnings.append(f"{slabel} : SKILL.md nomme un agent précis (« {hit.group(0)} ») — "
                                            "écrire « l'agent » pour rester portable")

    check_agents(os.path.join(ROOT, ".claude", "agents"), "dépôt")
    if not os.path.isfile(os.path.join(ROOT, "AGENTS.md")):
        errors.append("AGENTS.md manquant à la racine (instructions communes à tous les agents)")

    for w in warnings:
        print(f"⚠  {w}", file=sys.stderr)
    for e in errors:
        print(f"✖  {e}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} erreur(s).", file=sys.stderr)
        return 1
    print(f"✔  Dépôt valide{f' ({len(warnings)} avertissement(s))' if warnings else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
