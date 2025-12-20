from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
PDF_ROOT = ROOT_DIR / "pdfs"
COVERS_ROOT = ROOT_DIR / "covers"


def normalize_title(filename: str) -> str:
	from build_books_json import normalize_name  # type: ignore

	return normalize_name(filename)


def ensure_pymupdf():
	try:
		import fitz  # type: ignore  # noqa: F401
	except ImportError as exc:
		msg = (
			"PyMuPDF (fitz) yüklü değil. Lütfen önce kurun:\n"
			"  pip install PyMuPDF\n"
		)
		raise SystemExit(msg) from exc


def load_font(preferred: Optional[str] = None):
	from PIL import ImageFont  # type: ignore

	if preferred:
		try:
			return ImageFont.truetype(preferred, 40)
		except OSError:
			pass

	possible = [
		"C:/Windows/Fonts/DejaVuSans.ttf",
		"C:/Windows/Fonts/arial.ttf",
	]
	for path in possible:
		try:
			return ImageFont.truetype(path, 40)
		except OSError:
			continue

	return ImageFont.load_default()


def create_fallback_cover(output_path: Path, title: str) -> None:
	from PIL import Image, ImageDraw  # type: ignore

	width, height = 600, 800
	img = Image.new("RGB", (width, height), "#111111")
	draw = ImageDraw.Draw(img)

	for y in range(height):
		ratio = y / height
		r = int(20 + 40 * ratio)
		g = int(20 + 20 * ratio)
		b = int(40 + 80 * ratio)
		draw.line([(0, y), (width, y)], fill=(r, g, b))

	font = load_font()

	max_width = int(width * 0.8)
	words = title.split()
	lines = []
	current = ""
	for w in words:
		test = (current + " " + w).strip()
		w_size = draw.textlength(test, font=font)
		if w_size <= max_width:
			current = test
		else:
			if current:
				lines.append(current)
			current = w
	if current:
		lines.append(current)

	total_height = 0
	line_heights = []
	for line in lines:
		bbox = draw.textbbox((0, 0), line, font=font)
		h = bbox[3] - bbox[1]
		line_heights.append(h)
		total_height += h

	y = (height - total_height) // 2
	for i, line in enumerate(lines):
		w_len = draw.textlength(line, font=font)
		x = (width - w_len) // 2
		draw.text((x, y), line, font=font, fill="#FFFFFF")
		y += line_heights[i]

	output_path.parent.mkdir(parents=True, exist_ok=True)
	img.save(output_path, format="PNG")


def generate_cover_for_pdf(pdf_path: Path) -> None:
	import fitz  # type: ignore

	try:
		relative_from_root = pdf_path.relative_to(ROOT_DIR)
	except ValueError:
		return

	parts = list(relative_from_root.parts)
	if not parts or parts[0].lower() != "pdfs":
		return

	if len(parts) >= 3:
		# pdfs/Kategori/Dosya.pdf → covers/Kategori/Dosya.png
		category_folder = parts[1]
		output_dir = COVERS_ROOT / category_folder
	else:
		# pdfs/Dosya.pdf → covers/Dosya.png
		output_dir = COVERS_ROOT

	output_path = output_dir / (pdf_path.stem + ".png")

	title = normalize_title(pdf_path.name)

	try:
		doc = fitz.open(pdf_path)
		if doc.page_count == 0:
			raise RuntimeError("Boş PDF")
		page = doc.load_page(0)
		rect = page.rect
		target_width = 600
		zoom = target_width / rect.width if rect.width else 1.0
		matrix = fitz.Matrix(zoom, zoom)
		pix = page.get_pixmap(matrix=matrix)
		output_dir.mkdir(parents=True, exist_ok=True)
		pix.save(output_path.as_posix())
		doc.close()
		print(f"Kapak üretildi: {output_path}")
	except Exception as exc:  # noqa: BLE001
		print(f"PDF'den kapak üretilemedi, yedek oluşturuluyor: {pdf_path} ({exc})")
		create_fallback_cover(output_path, title)


def main() -> None:
	if not PDF_ROOT.exists():
		raise SystemExit(f"PDF klasörü bulunamadı: {PDF_ROOT}")

	ensure_pymupdf()

	try:
		import PIL  # type: ignore  # noqa: F401
	except ImportError:
		print(
			"Uyarı: Pillow (PIL) yüklü değil. Kapak üretimi çalışır, "
			"ama PDF okunamayan durumlarda fallback kapak oluşturmak için gereklidir.\n"
			"Kurmak için:\n  pip install Pillow\n",
			file=sys.stderr,
		)

	pdf_files = sorted(PDF_ROOT.rglob("*.pdf"))
	if not pdf_files:
		print(f"Hiç PDF bulunamadı: {PDF_ROOT}")
		return

	for pdf_path in pdf_files:
		generate_cover_for_pdf(pdf_path)


if __name__ == "__main__":
	main()
