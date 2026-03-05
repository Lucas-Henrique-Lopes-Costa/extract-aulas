#!/usr/bin/env python3
"""
Extrator de IFrames - Asimov Academy
Dado o link do curso, descobre todas as aulas e extrai os iframes.

Uso:
    python3 extract_iframes.py
"""

import time
import csv
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Configurar aqui ────────────────────────────────────────
URLS_FILE   = Path("urls.txt")
LESSON_PATH = "/curso/atividade/"   # padrão de URL das aulas
AFTER_LOAD  = 3                     # segundos aguardando JS
# ───────────────────────────────────────────────────────────


def read_course_urls() -> list[str]:
    if not URLS_FILE.exists():
        print(f"❌ {URLS_FILE} não encontrado.")
        exit(1)
    return [
        line.strip()
        for line in URLS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

CSV_FILE = Path("output") / "aulas.csv"   # arquivo fixo, incremental

PROFILE_DIR = Path("browser-profile")
OUTPUT_DIR  = Path("output")


def get_page_title(page) -> str:
    try:
        h1 = page.query_selector("h1")
        if h1:
            return h1.inner_text().strip()
    except Exception:
        pass
    return page.title().split("|")[0].strip()


def collect_lessons(page, course_url: str, lesson_path: str = LESSON_PATH) -> list[dict]:
    """Abre a página do curso e coleta todos os links de aulas."""
    page.goto(course_url, wait_until="domcontentloaded", timeout=20_000)
    time.sleep(AFTER_LOAD)

    course_name = get_page_title(page)
    print(f"  Curso: {course_name}")

    seen, lessons = set(), []
    for link in page.query_selector_all(f"a[href*='{lesson_path}']"):
        try:
            href  = link.get_attribute("href") or ""
            title = link.inner_text().strip()
            if href and href not in seen:
                seen.add(href)
                lessons.append({"course": course_name, "title": title, "url": href})
        except Exception:
            pass

    return lessons


def get_iframe(page, url: str) -> str:
    """Visita a aula e retorna o primeiro iframe src encontrado."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        time.sleep(AFTER_LOAD)
    except PlaywrightTimeout:
        return ""

    el = page.query_selector("iframe[src]")
    if el:
        return el.get_attribute("src") or ""
    return ""


def load_existing_urls() -> set[str]:
    """Retorna as URLs de aulas já registradas no CSV (para não duplicar)."""
    if not CSV_FILE.exists():
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return {row["iframe_src"] for row in csv.DictReader(f) if row["iframe_src"]}


def append_csv(rows: list[dict]):
    """Adiciona as novas linhas ao CSV fixo (sem apagar o que já existe)."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    is_new = not CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["curso", "aula", "iframe_src"])
        if is_new:
            w.writeheader()
        w.writerows(rows)
    print(f"\n  Arquivo: {CSV_FILE}")
    print(f"  +{len(rows)} linha(s) adicionada(s)")


def main():
    print("=" * 50)
    print("  Extrator de IFrames - Asimov Academy")
    print("=" * 50)

    PROFILE_DIR.mkdir(exist_ok=True)
    first_run = not any(PROFILE_DIR.iterdir())

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        if first_run:
            print("\n🌐 Faça login na plataforma.")
            page.goto("https://hub.asimov.academy/login/", timeout=20_000)
        else:
            print("🔐 Sessão anterior carregada")

        input("\n⏸  Pressione Enter quando estiver logado... ")

        existing_urls = load_existing_urls()
        all_rows = []

        for course_url in read_course_urls():
            print(f"\n📋 Coletando: {course_url}")

            # detecta o path das sub-aulas conforme o tipo de URL
            lesson_path = "/projeto/atividade/" if "/projeto/" in course_url else LESSON_PATH
            lessons = collect_lessons(page, course_url, lesson_path)

            if not lessons:
                print("  ⚠️  Nenhuma aula encontrada. Verifique LESSON_PATH no script.")
                continue

            print(f"  {len(lessons)} aula(s) encontrada(s)\n")

            for i, lesson in enumerate(lessons, 1):
                title = lesson["title"] or f"Aula {i}"
                print(f"  [{i:>3}/{len(lessons)}] {title[:60]}")

                src = get_iframe(page, lesson["url"])

                if src in existing_urls:
                    print("            ⏭  já registrado, pulando")
                    continue

                if src:
                    print(f"            ✅ {src[:85]}{'…' if len(src) > 85 else ''}")
                    existing_urls.add(src)
                else:
                    print("            ⚠️  sem iframe")

                all_rows.append({"curso": lesson["course"], "aula": title, "iframe_src": src})

        # 3. Salva CSV (incremental)
        append_csv(all_rows)
        ctx.close()
        print("\n✅ Concluído!")


if __name__ == "__main__":
    main()
