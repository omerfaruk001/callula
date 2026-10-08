/* Callula — istemci tarafı: sepet, favoriler, arama, galeri, menüler.
   Bağımlılık yok. Veriler sayfadaki #catalog JSON'undan okunur. */
(() => {
  "use strict";

  const CONFIG = {
    whatsapp: "905302023453",
    maxQty: 10,
  };

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;

  let CATALOG = {};
  try { CATALOG = JSON.parse($("#catalog").textContent); } catch (_) {}

  const tl = (n) => "₺" + n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icon = (n) => `<svg class="i" aria-hidden="true" focusable="false"><use href="/assets/icons.svg#${n}"/></svg>`;

  /* ---------- kalıcı durum (localStorage yoksa bellekte tutulur) ---------- */
  const memory = {};
  const store = {
    get(k, d) {
      try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (_) { return k in memory ? memory[k] : d; }
    },
    set(k, v) {
      try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) { memory[k] = v; }
    },
  };

  /* ---------- sepet ---------- */
  const cart = {
    items() { return store.get("callula.cart", []).filter((x) => CATALOG[x.s]); },
    save(list) { store.set("callula.cart", list); renderCart(); },
    add(slug, qty = 1) {
      const list = this.items();
      const row = list.find((x) => x.s === slug);
      if (row) row.q = Math.min(CONFIG.maxQty, row.q + qty);
      else list.push({ s: slug, q: Math.min(CONFIG.maxQty, qty) });
      this.save(list);
    },
    setQty(slug, qty) {
      const list = this.items();
      const row = list.find((x) => x.s === slug);
      if (!row) return;
      row.q = Math.max(1, Math.min(CONFIG.maxQty, qty || 1));
      this.save(list);
    },
    remove(slug) { this.save(this.items().filter((x) => x.s !== slug)); },
    count() { return this.items().reduce((a, x) => a + x.q, 0); },
    totals() {
      let sub = 0, list = 0;
      for (const x of this.items()) { sub += CATALOG[x.s].p * x.q; list += CATALOG[x.s].lp * x.q; }
      return { sub, list, saved: list - sub };
    },
  };

  function lineHTML(x) {
    const p = CATALOG[x.s];
    return `<li class="line" data-line="${x.s}">
      <a class="thumb" href="${p.u}" tabindex="-1" aria-hidden="true"><img src="${p.i}" alt="" width="80" height="100" loading="lazy"></a>
      <div>
        <div class="line-top"><a class="line-name" href="${p.u}">${esc(p.n)}</a></div>
        <p class="price"><span class="now">${tl(p.p)}</span><s class="was">${tl(p.lp)}</s></p>
        <div class="line-bottom">
          <div class="qty" data-qty data-line-qty="${x.s}"><button type="button" data-step="-1">${icon("minus")}<span class="sr">Adedi azalt</span></button><input type="number" value="${x.q}" min="1" max="${CONFIG.maxQty}" inputmode="numeric" aria-label="${esc(p.n)} adedi"><button type="button" data-step="1">${icon("plus")}<span class="sr">Adedi artır</span></button></div>
          <button class="line-remove" type="button" data-remove="${x.s}">Kaldır<span class="sr">: ${esc(p.n)}</span></button>
        </div>
      </div>
    </li>`;
  }

  function renderCart() {
    const items = cart.items();
    const n = cart.count();
    $$("[data-cart-count]").forEach((el) => { el.textContent = n || ""; el.dataset.n = n; });
    $$("[data-cart-count-text]").forEach((el) => { el.textContent = n ? `(${n})` : ""; });
    const t = cart.totals();
    $$("[data-cart-lines]").forEach((box) => {
      box.innerHTML = items.length
        ? `<ul class="line-items">${items.map(lineHTML).join("")}</ul>`
        : `<div class="empty"><p>Sepetinizde ürün bulunmamaktadır.</p><a class="btn" href="/urunler">Ürünleri keşfet</a></div>`;
    });
    $$("[data-cart-foot]").forEach((box) => {
      const inPage = !!box.closest("[data-cart-page]");
      box.hidden = !items.length;
      if (!items.length) { box.innerHTML = ""; return; }
      box.innerHTML = `<dl class="totals">
          <dt>Ara toplam</dt><dd>${tl(t.list)}</dd>
          <dt>İndirim</dt><dd>-${tl(t.saved)}</dd>
          <dt>Kargo</dt><dd>Ücretsiz</dd>
          <dt class="grand">Toplam (KDV dahil)</dt><dd class="grand">${tl(t.sub)}</dd>
        </dl>
        <button class="btn btn--block" type="button" data-checkout>${icon("whatsapp-logo")}WhatsApp ile sipariş ver</button>
        ${inPage ? "" : `<a class="btn btn--line btn--block" href="/sepet">Sepete git</a>`}
        <p class="meta-line">Siparişiniz, ürünler ve toplam tutarla birlikte WhatsApp mesajı olarak hazırlanır.</p>`;
    });
  }

  function checkout() {
    const items = cart.items();
    if (!items.length) return;
    const t = cart.totals();
    const lines = items.map((x) => `- ${CATALOG[x.s].n} x ${x.q} = ${tl(CATALOG[x.s].p * x.q)}`);
    const msg = ["Merhaba, aşağıdaki ürünleri sipariş vermek istiyorum:", ...lines, `Toplam (KDV dahil): ${tl(t.sub)}`].join("\n");
    window.open(`https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent(msg)}`, "_blank", "noopener");
  }

  /* ---------- favoriler ---------- */
  const favs = {
    list() { return store.get("callula.favs", []).filter((s) => CATALOG[s]); },
    has(s) { return this.list().includes(s); },
    toggle(s) {
      const l = this.list();
      store.set("callula.favs", l.includes(s) ? l.filter((x) => x !== s) : [...l, s]);
      renderFavs();
    },
  };

  function renderFavs() {
    const l = favs.list();
    $$("[data-fav]").forEach((b) => {
      const on = l.includes(b.dataset.fav);
      b.setAttribute("aria-pressed", String(on));
      const sr = $(".sr", b);
      if (sr) sr.textContent = `${CATALOG[b.dataset.fav]?.n || ""} ${on ? "favorilerden çıkar" : "favorilere ekle"}`;
      const lbl = $(".fav-label", b);
      if (lbl) lbl.textContent = on ? "Favorilerde" : "Favorilere ekle";
    });
    $$("[data-fav-count]").forEach((el) => { el.textContent = l.length || ""; el.dataset.n = l.length; });
    const grid = $("[data-fav-page]");
    if (grid) {
      $$("[data-card]", grid).forEach((li) => { li.hidden = !l.includes(li.dataset.card); });
      $("[data-fav-empty]").hidden = l.length > 0;
    }
  }

  /* ---------- dialoglar (sepet, mobil menü, lightbox) ---------- */
  function openDialog(d) {
    if (!d || d.open) return;
    d.showModal();
    document.body.classList.add("is-locked");
  }
  document.addEventListener("close", (ev) => {
    if (ev.target.tagName === "DIALOG" && !$("dialog[open]")) document.body.classList.remove("is-locked");
  }, true);
  $$("dialog").forEach((d) => {
    d.addEventListener("click", (ev) => { if (ev.target === d) d.close(); }); // backdrop
  });

  /* ---------- olay delegasyonu ---------- */
  document.addEventListener("click", (ev) => {
    const t = ev.target.closest("button, a");
    if (!t) return;
    if (t.dataset.add) {
      cart.add(t.dataset.add, 1);
      openDialog($("#sepet"));
      return;
    }
    if (t.dataset.fav) { favs.toggle(t.dataset.fav); return; }
    if (t.dataset.open) {
      const cur = t.closest("dialog");
      if (cur && cur.id !== t.dataset.open) cur.close();
      openDialog(document.getElementById(t.dataset.open));
      return;
    }
    if (t.hasAttribute("data-close")) { t.closest("dialog")?.close(); return; }
    if (t.dataset.remove) { cart.remove(t.dataset.remove); return; }
    if (t.hasAttribute("data-checkout")) { checkout(); return; }
    if (t.dataset.step) {
      const box = t.closest("[data-qty]");
      const input = $("input", box);
      const v = Math.max(1, Math.min(CONFIG.maxQty, (parseInt(input.value, 10) || 1) + Number(t.dataset.step)));
      input.value = v;
      if (box.dataset.lineQty) cart.setQty(box.dataset.lineQty, v);
    }
  });
  document.addEventListener("change", (ev) => {
    const box = ev.target.closest("[data-line-qty]");
    if (box) cart.setQty(box.dataset.lineQty, parseInt(ev.target.value, 10));
  });

  // Ürün detay: adet + sepete ekle
  $$("[data-buy]").forEach((f) => {
    f.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const q = Math.max(1, Math.min(CONFIG.maxQty, parseInt(f.adet.value, 10) || 1));
      cart.add(f.dataset.buy, q);
      openDialog($("#sepet"));
    });
  });

  // Mobil menüde bulunulan sayfayı işaretle
  $$("#mobil-menu a[href^='/']").forEach((a) => {
    if (a.getAttribute("href") === location.pathname.replace(/\/$/, "")) a.setAttribute("aria-current", "page");
  });

  /* ---------- header: yapışkan kenarlık ---------- */
  const header = $("[data-header]");
  const announce = $("[data-announce]");
  if (header && announce && "IntersectionObserver" in window) {
    new IntersectionObserver(([en]) => header.classList.toggle("is-stuck", !en.isIntersecting)).observe(announce);
  }

  /* ---------- Ürünler paneli ---------- */
  const megaBtn = $("[data-mega]");
  const mega = $("#urun-paneli");
  const searchBtn = $("[data-search-toggle]");
  const searchPanel = $("#arama-paneli");
  function setMega(open) {
    if (!megaBtn) return;
    megaBtn.setAttribute("aria-expanded", String(open));
    mega.hidden = !open;
    if (open) setSearch(false);
  }
  function setSearch(open) {
    if (!searchBtn) return;
    searchBtn.setAttribute("aria-expanded", String(open));
    searchPanel.hidden = !open;
    if (open) { setMega(false); $("[data-search-input]").focus(); }
  }
  if (megaBtn) {
    megaBtn.addEventListener("click", () => setMega(mega.hidden));
    if (finePointer) {
      let timer;
      const li = megaBtn.closest("li");
      const enter = () => { clearTimeout(timer); timer = setTimeout(() => setMega(true), 120); };
      const leave = () => { clearTimeout(timer); timer = setTimeout(() => setMega(false), 200); };
      li.addEventListener("mouseenter", enter); li.addEventListener("mouseleave", leave);
      mega.addEventListener("mouseenter", () => clearTimeout(timer)); mega.addEventListener("mouseleave", leave);
    }
    mega.addEventListener("focusout", (ev) => { if (!header.contains(ev.relatedTarget)) setMega(false); });
  }
  if (searchBtn) {
    searchBtn.addEventListener("click", () => setSearch(searchPanel.hidden));
    $("[data-search-close]").addEventListener("click", () => { setSearch(false); searchBtn.focus(); });
  }
  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Escape") return;
    if (mega && !mega.hidden) { setMega(false); megaBtn.focus(); }
    if (searchPanel && !searchPanel.hidden) { setSearch(false); searchBtn.focus(); }
  });
  document.addEventListener("click", (ev) => {
    if (header && !header.contains(ev.target)) { setMega(false); setSearch(false); }
  });

  /* ---------- arama ---------- */
  const norm = (s) => s.toLocaleLowerCase("tr-TR").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ı/g, "i");
  function search(q) {
    const terms = norm(q).split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    return Object.entries(CATALOG).filter(([, p]) => { const h = norm(p.q); return terms.every((t) => h.includes(t)); }).map(([s]) => s);
  }
  const sInput = $("[data-search-input]");
  const sResults = $("[data-search-results]");
  if (sInput) {
    sInput.addEventListener("input", () => {
      const q = sInput.value.trim();
      const hits = search(q);
      if (!q) { sResults.innerHTML = ""; return; }
      sResults.innerHTML = hits.length
        ? hits.map((s) => { const p = CATALOG[s]; return `<li><a href="${p.u}"><span class="thumb"><img src="${p.i}" alt="" width="64" height="80"></span><span><span class="nm">${esc(p.n)}</span><span class="pr">${tl(p.p)}</span></span></a></li>`; }).join("")
        : `<li class="search-empty">"${esc(q)}" için sonuç bulunamadı.</li>`;
    });
  }
  const sPage = $("[data-search-page]");
  if (sPage) {
    const q = new URLSearchParams(location.search).get("q") || "";
    sPage.value = q;
    const hits = search(q);
    $$("[data-search-grid] [data-card]").forEach((li) => { li.hidden = !hits.includes(li.dataset.card); });
    $("[data-search-summary]").textContent = q ? (hits.length ? `"${q}" için ${hits.length} ürün bulundu.` : `"${q}" için sonuç bulunamadı.`) : "Aramak istediğiniz ürünü ya da içeriği yazın.";
  }

  /* ---------- hero ürün şeridi: ürünler sırayla yukarı kayar ---------- */
  const chip = $("[data-chip]");
  if (chip && !reduceMotion) {
    const track = $(".chip-track", chip);
    const items = $$(".chip-item", track);
    // Kesintisiz döngü için ilk ürünün kopyası sona eklenir
    const clone = items[0].cloneNode(true);
    clone.setAttribute("aria-hidden", "true");
    $("a", clone).tabIndex = -1;
    track.appendChild(clone);
    let i = 0, paused = false;
    const setActive = (n) => items.forEach((li, j) => {
      const on = j === n % items.length;
      if (on) li.removeAttribute("aria-hidden"); else li.setAttribute("aria-hidden", "true");
      $("a", li).tabIndex = on ? 0 : -1;
    });
    const step = () => {
      if (paused || document.hidden) return;
      i += 1;
      track.style.transition = "";
      track.style.transform = `translateY(calc(var(--chip-h) * ${-i}))`;
      setActive(i);
    };
    track.addEventListener("transitionend", () => {
      if (i === items.length) { // kopyaya ulaşıldı: geçişsiz başa dön
        track.style.transition = "none";
        track.style.transform = "translateY(0)";
        i = 0;
      }
    });
    ["mouseenter", "focusin"].forEach((t) => chip.addEventListener(t, () => { paused = true; }));
    ["mouseleave", "focusout"].forEach((t) => chip.addEventListener(t, () => { paused = false; }));
    setInterval(step, 3200);
  }

  /* ---------- ana sayfa kategori indeksi ---------- */
  const catIndex = $("[data-cat-index]");
  if (catIndex) {
    const links = $$("[data-cat]", catIndex);
    const imgs = $$(".cat-visual img", catIndex);
    const activate = (i) => {
      links.forEach((l, j) => l.classList.toggle("is-active", i === j));
      imgs.forEach((im, j) => im.classList.toggle("is-active", i === j));
    };
    links.forEach((l, i) => { l.addEventListener("mouseenter", () => activate(i)); l.addEventListener("focus", () => activate(i)); });
  }

  /* ---------- sıralama ---------- */
  const sortSel = $("[data-sort]");
  if (sortSel) {
    const grid = $("[data-sortable]");
    sortSel.addEventListener("change", () => {
      const cards = $$("[data-card]", grid);
      const k = sortSel.value;
      cards.sort((a, b) => k === "asc" ? a.dataset.price - b.dataset.price : k === "desc" ? b.dataset.price - a.dataset.price : a.dataset.order - b.dataset.order);
      cards.forEach((c) => grid.appendChild(c));
    });
  }

  /* ---------- ürün galerisi ---------- */
  const gallery = $("[data-gallery]");
  if (gallery) {
    const track = $("[data-track]", gallery);
    const slides = $$(".slide", track);
    const thumbs = $$("[data-thumb]", gallery);
    const dots = $$(".dots span", gallery);
    let current = 0;
    const go = (i) => { track.scrollTo({ left: slides[i].offsetLeft, behavior: reduceMotion ? "auto" : "smooth" }); };
    thumbs.forEach((b) => b.addEventListener("click", () => go(Number(b.dataset.thumb))));
    const io = new IntersectionObserver((ens) => {
      ens.forEach((en) => {
        if (en.isIntersecting && en.intersectionRatio > 0.6) {
          current = Number(en.target.dataset.slide);
          thumbs.forEach((t, j) => t.setAttribute("aria-current", String(j === current)));
          dots.forEach((d, j) => d.classList.toggle("is-on", j === current));
        }
      });
    }, { root: track, threshold: [0.6] });
    slides.forEach((s) => io.observe(s));
    track.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowRight") { ev.preventDefault(); go(Math.min(slides.length - 1, current + 1)); }
      if (ev.key === "ArrowLeft") { ev.preventDefault(); go(Math.max(0, current - 1)); }
    });

    // Masaüstü: imleci takip eden yakınlaştırma
    if (finePointer) {
      slides.forEach((s) => {
        s.addEventListener("pointerenter", () => s.classList.add("is-zoom"));
        s.addEventListener("pointerleave", () => s.classList.remove("is-zoom"));
        s.addEventListener("pointermove", (ev) => {
          const r = s.getBoundingClientRect();
          s.style.setProperty("--zx", `${((ev.clientX - r.left) / r.width) * 100}%`);
          s.style.setProperty("--zy", `${((ev.clientY - r.top) / r.height) * 100}%`);
        });
      });
    }

    // Lightbox
    const lb = $("[data-lightbox]");
    if (lb) {
      let list = [];
      try { list = JSON.parse($("[data-lightbox-list]", lb).textContent); } catch (_) {}
      const lbImg = $("[data-lightbox-img]", lb);
      let idx = 0;
      const show = (i) => { idx = (i + list.length) % list.length; lbImg.src = list[idx]; lbImg.alt = `${$("h1").textContent} fotoğraf ${idx + 1}`; };
      const open = () => { show(current); openDialog(lb); };
      $("[data-lightbox-open]", gallery).addEventListener("click", open);
      slides.forEach((s) => s.addEventListener("click", open));
      $$("[data-lb]", lb).forEach((b) => b.addEventListener("click", () => show(idx + Number(b.dataset.lb))));
      lb.addEventListener("keydown", (ev) => {
        if (ev.key === "ArrowRight") show(idx + 1);
        if (ev.key === "ArrowLeft") show(idx - 1);
      });
    }
  }

  /* ---------- mobil satın alma çubuğu ---------- */
  const buybar = $("[data-buybar]");
  const mainCta = $("[data-main-cta]");
  if (buybar && mainCta && "IntersectionObserver" in window) {
    new IntersectionObserver(([en]) => {
      const show = !en.isIntersecting && en.boundingClientRect.top < 0;
      buybar.classList.toggle("is-shown", show);
      buybar.setAttribute("aria-hidden", String(!show));
      $("button", buybar).tabIndex = show ? 0 : -1;
    }).observe(mainCta);
  }

  /* ---------- e-bülten ---------- */
  $$("[data-newsletter]").forEach((form) => {
    const msg = $(".form-msg", form);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const email = form.email.value.trim();
      msg.classList.remove("is-error");
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
        msg.textContent = "Lütfen geçerli bir e-posta adresi yazın.";
        msg.classList.add("is-error");
        form.email.setAttribute("aria-invalid", "true");
        form.email.focus();
        return;
      }
      form.email.removeAttribute("aria-invalid");
      msg.textContent = "Gönderiliyor...";
      try {
        const res = await fetch(form.action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
        if (!res.ok) throw new Error(String(res.status));
        msg.textContent = "Teşekkürler, e-bülten listemize eklendiniz.";
        form.reset();
      } catch (_) {
        msg.textContent = "Kaydınızı şu anda alamadık. Lütfen daha sonra tekrar deneyin.";
        msg.classList.add("is-error");
      }
    });
  });

  renderCart();
  renderFavs();
  window.addEventListener("storage", (ev) => {
    if (ev.key === "callula.cart") renderCart();
    if (ev.key === "callula.favs") renderFavs();
  });
})();
