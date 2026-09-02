#!/usr/bin/env python3

import argparse
from pathlib import Path
import os
import re
import sys
import time

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


BASE_URL = "https://www.mypeopledoc.com"

DEFAULT_OUTPUT_DIR = (
    Path.home()
    / "Documents"
    / "Documents_MyPeopleDoc"
)

DEFAULT_PROFILE_DIR = (
    Path.home()
    / ".mypeopledoc-playwright-firefox"
)


# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """
    Cleans a name so it can be used as
    a file or folder name.
    """

    name = name.strip()

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name,
    )

    name = re.sub(
        r"\s+",
        " ",
        name,
    )

    return name or "Autres"


def detect_year(text: str) -> str:
    """
    Looks for a year in the title or the metadata.
    """

    years = re.findall(
        r"\b(19\d{2}|20\d{2})\b",
        text,
    )

    if years:
        return years[0]

    return "Annee_inconnue"


def unique_path(path: Path) -> Path:
    """
    Prevents overwriting an existing file.
    """

    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    i = 2

    while True:
        candidate = (
            parent
            / f"{stem}_{i}{suffix}"
        )

        if not candidate.exists():
            return candidate

        i += 1


# ----------------------------------------------------------------------
# Loading all documents
# ----------------------------------------------------------------------

def expand_all_documents(page):
    """
    Automatically clicks the
    'Afficher plus' button until it disappears.
    """

    print()
    print("Loading all documents...")

    while True:

        cards = page.locator(
            "[data-test-document-list-item]"
        )

        before = cards.count()

        load_more = page.locator(
            "button[data-test-load-more]"
        )

        # The button no longer exists:
        # everything is loaded.
        if load_more.count() == 0:
            break

        try:
            if not load_more.is_visible():
                break
        except Exception:
            break

        print(
            f"  {before} documents loaded..."
        )

        try:

            load_more.scroll_into_view_if_needed()

            load_more.click()

            # Wait until at least one new document
            # has been added to the DOM.
            page.wait_for_function(
                """
                previousCount => {
                    return document.querySelectorAll(
                        '[data-test-document-list-item]'
                    ).length > previousCount;
                }
                """,
                arg=before,
                timeout=15_000,
            )

        except PlaywrightTimeoutError:

            # Check one last time whether the button
            # simply disappeared.
            if (
                page.locator(
                    "button[data-test-load-more]"
                ).count()
                == 0
            ):
                break

            print(
                "  ⚠ no new document after "
                "'Afficher plus'."
            )

            break

        # Small delay to let Ember finish
        # its updates.
        page.wait_for_timeout(300)

    total = page.locator(
        "[data-test-document-list-item]"
    ).count()

    print()
    print(
        f"✓ {total} documents loaded."
    )

    return total


# ----------------------------------------------------------------------
# Extracting information from a card
# ----------------------------------------------------------------------

def get_document_info(card):
    """
    Gets title, type and year from a card.
    """

    # --------------------------------------------------------------
    # Title
    # --------------------------------------------------------------

    title_locator = card.locator(
        ".doc-title"
    )

    if title_locator.count():
        title = (
            title_locator
            .first
            .inner_text()
            .strip()
        )
    else:
        title = "Document"

    # --------------------------------------------------------------
    # Full text of the card
    # --------------------------------------------------------------

    try:
        card_text = card.inner_text()
    except Exception:
        card_text = title

    # --------------------------------------------------------------
    # Type = MyPeopleDoc label
    #
    # Observed example:
    #
    # <span class="pin ...">
    #     <em>Bulletin de paie</em>
    # </span>
    # --------------------------------------------------------------

    labels = card.locator(
        "span.pin em"
    )

    if labels.count():

        doc_type = (
            labels
            .first
            .inner_text()
            .strip()
        )

    else:

        # basic fallback
        lowered = title.lower()

        if (
            "bulletin" in lowered
            or "salaire" in lowered
            or "paie" in lowered
        ):
            doc_type = "Bulletin de paie"

        elif "attestation" in lowered:
            doc_type = "Attestations"

        elif "contrat" in lowered:
            doc_type = "Contrats"

        else:
            doc_type = "Autres"

    year = detect_year(
        f"{title} {card_text}"
    )

    return {
        "title": title,
        "type": doc_type,
        "year": year,
    }


# ----------------------------------------------------------------------
# Download
# ----------------------------------------------------------------------

def download_all_documents(page, output_dir):

    # First load the WHOLE list.
    total = expand_all_documents(page)

    if total == 0:
        print(
            "No document found."
        )
        return 0, 0

    successes = 0
    failures = 0

    print()
    print(
        "Downloading documents..."
    )
    print()

    for index in range(total):

        # The locator is recreated at each iteration.
        # This is more robust with Ember.
        cards = page.locator(
            "article.document-cards"
        )

        if index >= cards.count():
            break

        card = cards.nth(index)

        info = get_document_info(card)

        title = info["title"]
        doc_type = info["type"]
        year = info["year"]

        print(
            f"[{index + 1}/{total}] "
            f"{title}"
        )

        # ----------------------------------------------------------
        # Download link of THIS card
        # ----------------------------------------------------------

        download_link = card.locator(
            "a.download"
        )

        if download_link.count() == 0:

            # fallback based on the observed URL
            download_link = card.locator(
                'a[href*="/api/documents/"]'
                '[href$="/download"]'
            )

        if download_link.count() == 0:

            print(
                "  ⚠ download link not found"
            )

            failures += 1
            continue

        # ----------------------------------------------------------
        # Destination folder
        # ----------------------------------------------------------

        target_dir = (
            output_dir
            / safe_filename(doc_type)
            / year
        )

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            download_link.scroll_into_view_if_needed()

            # Playwright intercepts the download
            with page.expect_download(
                timeout=30_000
            ) as download_info:

                download_link.click()

            download = download_info.value

            suggested_name = (
                download.suggested_filename
            )

            if not suggested_name:

                suggested_name = (
                    safe_filename(title)
                    + ".pdf"
                )

            target = unique_path(
                target_dir
                / safe_filename(
                    suggested_name
                )
            )

            download.save_as(
                target
            )

            print(
                f"  ✓ {doc_type}/{year}/"
                f"{target.name}"
            )

            successes += 1

        except PlaywrightTimeoutError:

            print(
                "  ⚠ timeout during download"
            )

            failures += 1

        except Exception as exc:

            print(
                f"  ⚠ error: {exc}"
            )

            failures += 1

        # Do not send too many simultaneous requests
        time.sleep(0.3)

    return successes, failures


# ----------------------------------------------------------------------
# Main program
# ----------------------------------------------------------------------

def parse_args(argv=None):
    """
    Gets the command line options.
    """

    parser = argparse.ArgumentParser(
        description="Export MyPeopleDoc documents, sorted by type / year."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Destination folder "
            f"(default: {DEFAULT_OUTPUT_DIR})."
        ),
    )

    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=DEFAULT_PROFILE_DIR,
        help=(
            "Persistent Firefox session folder "
            f"(default: {DEFAULT_PROFILE_DIR})."
        ),
    )

    return parser.parse_args(argv)


def main():
    args = parse_args()

    # When running from the PyInstaller executable, the Firefox browser
    # is bundled inside it (the .local-browsers folder of the playwright
    # package). We then force the browser lookup to happen within that
    # package rather than in the user cache.
    if getattr(sys, "frozen", False):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

    output_dir = args.output
    profile_dir = args.profile_dir

    # Some Windows consoles (cp1252) cannot
    # display ✓ / ⚠.
    try:
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        pass

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "===================================="
    )
    print(
        " Export MyPeopleDoc"
    )
    print(
        "===================================="
    )
    print()
    print(
        f"Destination: {output_dir}"
    )
    print()

    with sync_playwright() as p:

        browser = (
            p.firefox
            .launch_persistent_context(
                user_data_dir=str(
                    profile_dir
                ),
                headless=False,
                accept_downloads=True,
                viewport={
                    "width": 1440,
                    "height": 950,
                },
            )
        )

        if browser.pages:
            page = browser.pages[0]
        else:
            page = browser.new_page()

        print(
            "Opening MyPeopleDoc..."
        )

        page.goto(
            BASE_URL,
            wait_until="domcontentloaded",
        )

        print()
        print(
            "1. Log in normally "
            "in Firefox."
        )
        print(
            "2. Go to 'Mes documents'."
        )
        print(
            "3. Do NOT click on "
            "'Afficher plus': "
            "the script will do it."
        )
        print()

        input(
            "When the 'Mes documents' page "
            "is displayed, press Enter here..."
        )

        # MyPeopleDoc is an Ember SPA.
        # We give the DOM a little time to stabilize.
        page.wait_for_timeout(
            2_000
        )

        # Minimal check
        documents = page.locator(
            "[data-test-document-list-item]"
        )

        if documents.count() == 0:

            print()
            print(
                "⚠ No document detected."
            )
            print(
                "Make sure you are on "
                "the 'Mes documents' page."
            )

            browser.close()
            return

        successes, failures = (
            download_all_documents(
                page,
                output_dir,
            )
        )

        print()
        print(
            "===================================="
        )
        print(
            " Export finished"
        )
        print(
            "===================================="
        )
        print()
        print(
            f"Succeeded: {successes}"
        )
        print(
            f"Failures : {failures}"
        )
        print()
        print(
            f"Folder: {output_dir}"
        )
        print()

        input(
            "Press Enter to close Firefox..."
        )

        browser.close()


if __name__ == "__main__":
    main()
