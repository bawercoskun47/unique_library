import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const PDF_DIR = path.join(ROOT, "pdfs");
const COVERS_DIR = path.join(ROOT, "covers");
const OUTPUT = path.join(ROOT, "books.json");

// Basit yardımcı: Dosya adına göre insan okunabilir başlık
function toTitle(filename) {
  const base = filename.replace(/\.[^/.]+$/, ""); // uzantıyı sil
  return base
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

// Varsayılan kategori (istersen dosya adına göre ayırabilirsin)
function guessCategory(filename) {
  const lower = filename.toLowerCase();
  if (lower.includes("ai") || lower.includes("yapay")) return "Yapay Zeka";
  if (lower.includes("code") || lower.includes("yazilim")) return "Yazılım";
  if (lower.includes("kitap") || lower.includes("roman")) return "Kitaplar";
  return "Diğer";
}

function findCover(baseName, covers) {
  const candidates = [
    `${baseName}.jpg`,
    `${baseName}.jpeg`,
    `${baseName}.png`,
    `${baseName}.webp`,
  ];
  for (const c of candidates) {
    if (covers.has(c)) return `covers/${c}`;
  }
  return null;
}

async function main() {
  if (!fs.existsSync(PDF_DIR)) {
    console.error("Hata: pdfs klasörü bulunamadı.");
    process.exit(1);
  }

  if (!fs.existsSync(COVERS_DIR)) {
    console.error("Uyarı: covers klasörü yok. Kapaksız kartlar oluşturulacak.");
  }

  const pdfFiles = fs
    .readdirSync(PDF_DIR)
    .filter((f) => f.toLowerCase().endsWith(".pdf"))
    .sort((a, b) => a.localeCompare(b, "tr"));

  const coverFiles = fs.existsSync(COVERS_DIR)
    ? new Set(fs.readdirSync(COVERS_DIR))
    : new Set();

  const items = pdfFiles.map((file) => {
    const base = file.replace(/\.[^/.]+$/, "");
    const title = toTitle(file);
    const category = guessCategory(file);
    const cover = findCover(base, coverFiles);

    return {
      title,
      file: `pdfs/${file}`,
      cover: cover || undefined,
      category,
      year: new Date().getFullYear(),
      tags: [],
    };
  });

  fs.writeFileSync(OUTPUT, JSON.stringify(items, null, 2), "utf8");
  console.log(
    `books.json güncellendi. Toplam ${items.length} PDF işlendi.\n${OUTPUT}`
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
