async function loadBooks() {
  const container = document.getElementById("app");

  try {
    const res = await fetch("books_min.json", { cache: "no-store" });
    if (!res.ok) {
      throw new Error("books_min.json yüklenemedi: " + res.status);
    }
    const books = await res.json();
    return books;
  } catch (error) {
    console.error(error);
    container.innerHTML =
      '<div class="error-message">Veriler yüklenirken bir hata oluştu.\n<br/>books_min.json dosyasının repo kökünde olduğundan ve bir HTTP sunucusu üzerinden servis edildiğinden emin olun.</div>';
    return null;
  }
}

function groupByCategory(books) {
  const map = new Map();
  for (const book of books) {
    const key = book.category || "Genel";
    if (!map.has(key)) {
      map.set(key, []);
    }
    map.get(key).push(book);
  }
  return map;
}

function createRowElement(category, books) {
  const row = document.createElement("section");
  row.className = "row";

  const header = document.createElement("div");
  header.className = "row-header";

  const title = document.createElement("h2");
  title.className = "row-title";
  title.textContent = category;

  const count = document.createElement("span");
  count.className = "row-count";
  count.textContent = `${books.length} kitap`;

  header.appendChild(title);
  header.appendChild(count);

  const scroller = document.createElement("div");
  scroller.className = "row-scroller";

  for (const book of books) {
    const link = document.createElement("a");
    link.className = "card-link";
    link.href = book.file;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    const card = document.createElement("article");
    card.className = "card";
    card.style.backgroundImage = `url(${book.cover})`;

    const badge = document.createElement("div");
    badge.className = "card-badge";
    badge.textContent = "PDF";

    const overlay = document.createElement("div");
    overlay.className = "card-overlay";

    const titleEl = document.createElement("h3");
    titleEl.className = "card-title";
    titleEl.textContent = book.title;

    const catEl = document.createElement("p");
    catEl.className = "card-category";
    catEl.textContent = book.category;

    overlay.appendChild(titleEl);
    overlay.appendChild(catEl);

    card.appendChild(badge);
    card.appendChild(overlay);
    link.appendChild(card);
    scroller.appendChild(link);
  }

  row.appendChild(header);
  row.appendChild(scroller);
  return row;
}

function render(books, query) {
  const container = document.getElementById("app");
  container.innerHTML = "";

  const trimmedQuery = (query || "").trim().toLowerCase();

  let filtered = books;
  if (trimmedQuery) {
    filtered = books.filter((b) => {
      return (
        b.title.toLowerCase().includes(trimmedQuery) ||
        (b.category && b.category.toLowerCase().includes(trimmedQuery))
      );
    });
  }

  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML =
      "Eşleşen kitap bulunamadı. <br/><br/><strong>" +
      trimmedQuery +
      "</strong> için sonuç yok.";
    container.appendChild(empty);
    return;
  }

  const byCat = groupByCategory(filtered);

  const categories = Array.from(byCat.keys()).sort((a, b) =>
    a.localeCompare(b, "tr", { sensitivity: "base" })
  );

  for (const cat of categories) {
    const row = createRowElement(cat, byCat.get(cat));
    container.appendChild(row);
  }
}

async function bootstrap() {
  const books = await loadBooks();
  if (!books) return;

  let currentQuery = "";
  render(books, currentQuery);

  const searchInput = document.getElementById("search-input");
  if (!searchInput) return;

  let debounceId = null;
  function scheduleRender(value) {
    if (debounceId) {
      window.clearTimeout(debounceId);
    }
    debounceId = window.setTimeout(() => {
      currentQuery = value;
      render(books, currentQuery);
    }, 160);
  }

  searchInput.addEventListener("input", (ev) => {
    const value = ev.target.value || "";
    scheduleRender(value);
  });
}

window.addEventListener("DOMContentLoaded", () => {
  bootstrap();
});
