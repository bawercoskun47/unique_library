from __future__ import annotations

import json
import locale
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


ROOT_DIR = Path(__file__).resolve().parents[1]
PDF_ROOT = ROOT_DIR / "pdfs"
BOOKS_JSON = ROOT_DIR / "books.json"
BOOKS_MIN_JSON = ROOT_DIR / "books_min.json"


@dataclass
class Book:
	title: str
	category: str
	file: str
	cover: str
	year: str = ""
	tags: List[str] | None = None


def safe_set_turkish_locale() -> None:
	"""Try to set a Turkish-friendly locale for sorting; silently ignore failures."""

	candidates = [
		"tr_TR.UTF-8",
		"tr_TR.utf8",
		"tr_TR",
		"Turkish_Turkey.1254",
	]
	for loc in candidates:
		try:
			locale.setlocale(locale.LC_COLLATE, loc)
			return
		except locale.Error:
			continue


def normalize_name(raw: str) -> str:
	"""Dosya/klasör adını insan okunur hale çevirir."""

	name = raw
	if "." in name:
		name = name.rsplit(".", 1)[0]

	name = re.sub(r"^[0-9_\-\s]+", "", name)
	name = name.replace("_", " ")
	name = re.sub(r"\s+", " ", name)
	return name.strip().title()


def derive_category_label(category_folder: str) -> str:
	return normalize_name(category_folder)


def build_books() -> list[Book]:
	if not PDF_ROOT.exists():
		raise SystemExit(f"PDF klasörü bulunamadı: {PDF_ROOT}")

	books: list[Book] = []

	for pdf_path in sorted(PDF_ROOT.rglob("*.pdf")):
		try:
			relative_from_root = pdf_path.relative_to(ROOT_DIR)
		except ValueError:
			continue

		parts = list(relative_from_root.parts)

		# Beklenen yollar:
		# - pdfs/Dosya.pdf          (kategori yok, hepsi tek klasörde)
		# - pdfs/Kategori/Dosya.pdf (ilk seviye klasör kategori)
		if not parts or parts[0].lower() != "pdfs":
			continue

		if len(parts) >= 3:
			# Klasörlü yapı: pdfs/01_anarsizm/Dosya.pdf
			category_folder = parts[1]
			category_label = derive_category_label(category_folder)
			cover_rel_posix = (
				Path("covers") / category_folder / (pdf_path.stem + ".png")
			)
		else:
			# Düz yapı: pdfs/Dosya.pdf → kategori: Genel
			category_folder = ""
			category_label = "Genel"
			cover_rel_posix = Path("covers") / (pdf_path.stem + ".png")

		file_rel_posix = relative_from_root.as_posix()
		title = normalize_name(pdf_path.name)

		book = Book(
			title=title,
			category=category_label,
			file=file_rel_posix,
			cover=cover_rel_posix.as_posix(),
			year="",
			tags=[],
		)
		books.append(book)

	safe_set_turkish_locale()
	collate_key = locale.strxfrm
	books.sort(key=lambda b: (collate_key(b.category), collate_key(b.title)))
	return books


def write_json_files(books: list[Book]) -> None:
	data_full = [asdict(b) for b in books]
	BOOKS_JSON.write_text(
		json.dumps(data_full, ensure_ascii=False, indent=2), encoding="utf-8"
	)

	data_min = [
		{
			"title": b.title,
			"category": b.category,
			"file": b.file,
			"cover": b.cover,
		}
		for b in books
	]
	BOOKS_MIN_JSON.write_text(
		json.dumps(data_min, ensure_ascii=False, separators=(",", ":")),
		encoding="utf-8",
	)


def main() -> None:
	books = build_books()
	write_json_files(books)
	print(f"{len(books)} kitap kaydı üretildi.")
	print(f"Tam içerik: {BOOKS_JSON}")
	print(f"Hafif sürüm: {BOOKS_MIN_JSON}")


if __name__ == "__main__":
	main()
