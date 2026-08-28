"""Generate the phase-one interactive exercise manifest.

The controls intentionally contain no marking, submit, reset, or result logic.
They mirror the printed prompts and save unfinished answers locally so the next
phase can add assessment behaviour without replacing the page content.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "tools" / "source-maps"
OUTPUT = ROOT / "content" / "exercises.json"
SCRIPT_OUTPUT = ROOT / "content" / "exercises.js"

INTERACTIVE_PAGES = {
    8, 9, 10, 12, 13, 15, 17, 18, 19, 22, 23, 26, 27, 30, 31,
    33, 34, 36, 37, 39, 41, 42, 44, 46, 47, 49, 50, 53, 55, 56,
    57, 59, 60, 62, 64, 65, 67, 68, 71, 72,
}

# These pages contain tightly spaced printed questions with no room for an
# additional answer line. Their questions are reflowed inside the original
# exercise box so every prompt owns a clean field directly underneath it.
STACKED_PAGES = {
    10, 15, 17, 18, 22, 23, 27, 31, 33, 34, 36, 37, 41, 44, 46,
    53, 55, 56, 57, 64, 65, 67, 72,
}

COMMAND = re.compile(
    r"^(?:Andika|Taja|Eleza|Orodhesha|Chora|Oanisha|Panga|Tunga|Bainisha|Jaza)\b",
    re.I,
)
HEADING = re.compile(
    r"^(?:Zoezi|Maswali|Kazi ya kufanya|Wimbo|Utangulizi|Vifaa|Hatua|Tabia njema|Sura)\b",
    re.I,
)


def clean(value: str) -> str:
    return " ".join(
        value.replace("â€™", "’").replace("â€“", "–").replace("Ã—", "×").split()
    )


def segments(page: int) -> list[str]:
    data = json.loads((MAP_DIR / f"pg{page:03d}.json").read_text(encoding="utf-8"))
    result = []
    for item in data["transcript"]:
        value = clean(item["text"])
        if not value or ".indd" in value or re.fullmatch(r"(?:\d+|[ivxlcdm]+)", value, re.I):
            continue
        result.append(value)
    return result


def title_for(page: int, values: list[str]) -> str:
    for value in values:
        if re.match(r"^Zoezi la\b", value, re.I):
            return value
    if any(re.match(r"^Maswali\b", value, re.I) for value in values):
        return "Maswali"
    return f"Sehemu ya kujibu — ukurasa {page}"


def extract_prompts(page: int) -> list[str]:
    values = segments(page)
    prompts = []
    index = 0
    while index < len(values):
        value = re.sub(r"^(?:\(?[a-z]\)|\d+\.)\s*", "", values[index], flags=re.I)
        is_prompt = bool(COMMAND.match(value) or "?" in value)
        if is_prompt and not re.match(r"^(?:Jibu maswali|Jaza nafasi|Oanisha kifaa|Oanisha sehemu)", value, re.I):
            combined = value
            lookahead = index + 1
            while (
                not re.search(r"[.?!:]$", combined)
                and lookahead < len(values)
                and lookahead <= index + 2
            ):
                next_value = values[lookahead]
                if HEADING.match(next_value) or re.fullmatch(r"(?:\(?[a-z]\)|\d+\.)", next_value, re.I):
                    break
                combined += " " + next_value
                lookahead += 1
            combined = clean(combined)
            if len(combined) >= 12 and combined not in prompts:
                prompts.append(combined)
            index = max(index + 1, lookahead)
        else:
            index += 1
    return prompts[:10]


def field_type(prompt: str) -> str:
    if re.match(r"^(?:Eleza|Chora|Panga|Tunga|Kwa nini|Unawezaje|Utafanya|Andika sentensi)", prompt, re.I):
        return "textarea"
    return "textarea" if len(prompt) > 92 else "text"


def generic_page(page: int) -> dict:
    values = segments(page)
    prompts = extract_prompts(page)
    return {
        "title": title_for(page, values),
        "items": [
            {
                "id": f"p{page}-q{index}",
                "type": field_type(prompt),
                "prompt": prompt,
            }
            for index, prompt in enumerate(prompts, 1)
        ],
    }


def select_item(item_id: str, prompt: str, options: list[str]) -> dict:
    return {"id": item_id, "type": "select", "prompt": prompt, "options": options}


SPECIAL = {
    9: {
        "title": "Zoezi la 1 — Rangi za maumbo",
        "items": [
            {
                "id": f"p9-shape-{number}",
                "type": "radio",
                "anchor": f"{number}.",
                "position": [
                    {"left": 19, "top": 29.5, "width": 23},
                    {"left": 44, "top": 29.5, "width": 23},
                    {"left": 70, "top": 29.5, "width": 18},
                    {"left": 28, "top": 51.8, "width": 23},
                    {"left": 70, "top": 51.8, "width": 18},
                ][number - 1],
                "prompt": f"Umbo namba {number} lina rangi gani?",
                "options": ["Bluu", "Nyekundu", "Kijani", "Waridi", "Njano"],
            }
            for number in range(1, 6)
        ],
    },
    13: {
        "title": "Zoezi la 4 — Oanisha sehemu ya mwili na kazi yake",
        "items": [
            {
                "id": "p13-matching",
                "type": "matching",
                "options": ["kushika vitu", "kutembea", "kunusa", "kusikia", "kuongea na kula", "kuona"],
                "rows": [
                    {"id": "macho", "prompt": "Macho", "anchor": "kushika vitu", "replace": True},
                    {"id": "mdomo", "prompt": "Mdomo", "anchor": "kutembea", "replace": True},
                    {"id": "sikio", "prompt": "Sikio", "anchor": "kunusa", "replace": True},
                    {"id": "miguu", "prompt": "Miguu", "anchor": "kusikia", "replace": True},
                    {"id": "mikono", "prompt": "Mikono", "anchor": "kuongea na kula", "replace": True},
                    {"id": "pua", "prompt": "Pua", "anchor": "kuona", "replace": True},
                ],
            }
        ],
    },
    39: {
        "title": "Mazoezi ya 8 na 9",
        "items": [
            {"id": "p39-order", "type": "textarea", "prompt": "Panga sentensi kwa mtiririko wa matukio katika picha."},
            select_item("p39-blank-1", "Joto la pasi huua…", ["vijidudu", "unyevu", "chafu", "kabati"]),
            select_item("p39-blank-2a", "Unapopiga nguo pasi, unaweka nini juu ya meza?", ["shuka", "kabati", "vijidudu", "unyevu"]),
            select_item("p39-blank-2b", "Unapopiga nguo pasi, unaweka nguo juu ya nini?", ["meza", "kabati", "shuka", "vijidudu"]),
            select_item("p39-blank-3", "Tunatundika nguo baada ya kupiga pasi ili…", ["zisipate unyevu", "ziwe chafu", "ziwe na vijidudu", "ziwekwe mezani"]),
            select_item("p39-blank-4", "Tunahifadhi nguo iliyonyooshwa kwenye…", ["kabati", "meza", "shuka", "unyevu"]),
        ],
    },
    47: {
        "title": "Zoezi la 12 — Jaza nafasi",
        "items": [
            select_item("p47-blank-1", "Kifaa cha ncha kali ni…", ["Dodoki", "VVU", "UKIMWI", "kusisitiza", "glovu", "sindano"]),
            select_item("p47-blank-2", "Kifaa kinachotumika kusugua mwili unapooga ni…", ["Dodoki", "VVU", "UKIMWI", "kusisitiza", "glovu", "sindano"]),
            select_item("p47-blank-3", "Kifaa kinachovaliwa mkononi ili kujikinga na maambukizi ya VVU ni…", ["Dodoki", "VVU", "UKIMWI", "kusisitiza", "glovu", "sindano"]),
        ],
    },
    50: {
        "title": "Zoezi la 1 — Oanisha kifaa na kazi yake",
        "items": [
            {
                "id": "p50-matching",
                "type": "matching",
                "options": ["Fagio", "Jembe", "Reki", "Pipa la takataka", "Mkasi", "Koleo la takataka"],
                "rows": [
                    {"id": "vumbi", "prompt": "Huondoa vumbi na uchafu"},
                    {"id": "kulimia", "prompt": "Hutumika kulimia"},
                    {"id": "kukusanya", "prompt": "Hutumika kukusanya nyasi na takataka"},
                    {"id": "kuhifadhi", "prompt": "Hutumika kuhifadhi takataka kabla ya kuzitupa shimoni"},
                    {"id": "maua", "prompt": "Hutumika kukatia maua"},
                    {"id": "kubebea", "prompt": "Hubebea takataka baada ya kufagia"},
                ],
            }
        ],
    },
    56: {
        "title": "Zoezi la 2 — Mazingira hatarishi",
        "items": [
            {"id": "p56-q1", "type": "text", "prompt": "Taja vitendo hatarishi katika mazingira yako."},
            {"id": "p56-q2", "type": "textarea", "prompt": "Unawezaje kujiepusha na mazingira hatarishi?"},
            {"id": "p56-q3", "type": "textarea", "prompt": "Utafanya nini ukimuona rafiki yako anacheza barabarani?"},
            {"id": "p56-q4", "type": "textarea", "prompt": "Ukiogelea kwenye maji marefu utapata madhara gani?"},
            {
                "id": "p56-safety",
                "type": "true_false",
                "prompt": "5. Kati ya matendo yafuatayo ni yapi hatarishi?",
                "rows": [
                    {"id": "miti", "prompt": "Kupanda juu ya miti mirefu"},
                    {"id": "nyumbani", "prompt": "Kusaidia kazi za nyumbani"},
                    {"id": "giza", "prompt": "Kucheza sehemu zenye giza"},
                    {"id": "kufagia", "prompt": "Kufagia uwanja"},
                    {"id": "ncha", "prompt": "Kuchezea wembe, kisu au vitu vyenye ncha kali"},
                ],
            },
            {"id": "p56-q6", "type": "text", "prompt": "Andika tabia hatarishi unazozifahamu.", "below": True},
        ],
    },
    60: {
        "title": "Zoezi la 4 — Maana za alama",
        "items": [
            {"id": "p60-sign-1", "type": "text", "prompt": "Andika maana ya alama ya 1.", "position": {"left": 18, "top": 30.2, "width": 28}},
            {"id": "p60-sign-2", "type": "text", "prompt": "Andika maana ya alama ya 2.", "position": {"left": 55, "top": 30.2, "width": 28}},
            {"id": "p60-sign-3", "type": "text", "prompt": "Andika maana ya alama ya 3.", "position": {"left": 18, "top": 49.2, "width": 28}},
            {"id": "p60-sign-4", "type": "text", "prompt": "Andika maana ya alama ya 4.", "position": {"left": 55, "top": 49.2, "width": 28}},
        ],
    },
}


def main() -> None:
    pages = {}
    for page in sorted(INTERACTIVE_PAGES):
        entry = SPECIAL.get(page) or generic_page(page)
        if entry["items"]:
            if page in STACKED_PAGES:
                entry["layout"] = "stacked"
            pages[str(page)] = entry
    manifest = {"version": 8, "pages": pages}
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    SCRIPT_OUTPUT.write_text(
        "window.AFYA_EXERCISES = " + json.dumps(manifest, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"Built exercise controls for {len(pages)} pages.")


if __name__ == "__main__":
    main()
