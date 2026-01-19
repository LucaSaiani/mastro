document.addEventListener("DOMContentLoaded", () => {
    const menu = document.querySelector(".menu");
    const menuList = document.getElementById("menu-list");
    const pageDiv = document.querySelector(".page");

    // ======================= Helper: Gestione immagini dinamiche =======================
    function setImagePaths(basePath, container = document) {
        if (!basePath) return;

        console.log("Base path immagini:", basePath);

        const headerImg = container.querySelector('.auto-image-header');
        if (headerImg) headerImg.src = basePath + "icon.png";

        const topRightImg = container.querySelector('.auto-image-top-right');
        if (topRightImg) topRightImg.src = basePath + "thumbnail.png";

        const exampleImgs = container.querySelectorAll('.auto-image-example');
        exampleImgs.forEach((img, index) => {
            const imageName = img.dataset.image || `example_0${index + 1}`;
            img.src = basePath + imageName + ".png";
        });
    }

    // ======================= Menu: Funzioni di gestione =======================
    function closeAllSubmenus(excludeLi = null) {
        menu.querySelectorAll(".has-submenu.open").forEach(openLi => {
            let isExcluded = false;
            let current = excludeLi;

            while (current) {
                if (openLi === current) {
                    isExcluded = true;
                    break;
                }
                current = current.parentElement.closest("li");
            }

            if (!isExcluded) openLi.classList.remove("open");
        });
    }

    function openMenuToLi(targetLi) {
        if (!targetLi) return;
        let current = targetLi;
        while (current) {
            if (current.classList.contains("has-submenu")) {
                current.classList.add("open");
            }
            current = current.parentElement.closest("li");
        }
    }

    function attachPageInternalLinks() {
        pageDiv.querySelectorAll("a[data-page]").forEach(link => {
            link.addEventListener("click", e => {
                e.preventDefault();
                loadPage(link.getAttribute("data-page"));
            });
        });
    }

    function attachSubmenuListeners(container) {
        container.querySelectorAll("li[data-page]").forEach(li => {
            if (li.dataset.listenerAttached) return;

            li.addEventListener("click", e => {
                e.stopPropagation(); 
                const targetLi = e.currentTarget;
                const page = targetLi.getAttribute("data-page");

                if (targetLi.classList.contains("has-submenu")) {
                    targetLi.parentElement.querySelectorAll(".has-submenu.open").forEach(sibling => {
                        if (sibling !== targetLi) sibling.classList.remove("open");
                    });
                    targetLi.classList.toggle("open");
                    closeAllSubmenus(targetLi);
                }

                loadPage(page, targetLi);
            });

            li.dataset.listenerAttached = true;
        });
    }

    // ======================= 🔹 Solo link in <h1> e <h2> =======================
    function recursivelyLoadSubmenu(parentLi, pageFile) {
        const submenuUl = parentLi.querySelector("ul.submenu");
        if (!submenuUl) return; 

        fetch(pageFile)
            .then(r => (r.ok ? r.text() : Promise.reject(`Submenu file not found: ${pageFile}`)))
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                // 🔹 Solo link in h1 o h2
                const links = doc.querySelectorAll("h1 a[data-page], h2 a[data-page]");

                if (links.length > 0) {
                    parentLi.classList.add("has-submenu");
                    submenuUl.innerHTML = "";

                    links.forEach(link => {
                        const newPage = link.getAttribute("data-page");
                        const linkText = link.textContent.trim() || newPage;

                        const newLi = document.createElement("li");
                        const contentWrapper = document.createElement("span");
                        contentWrapper.classList.add("menu-title-content");
                        contentWrapper.textContent = linkText;
                        newLi.appendChild(contentWrapper);
                        newLi.setAttribute("data-page", newPage);

                        const subUl = document.createElement("ul");
                        subUl.classList.add("submenu");
                        newLi.appendChild(subUl);

                        submenuUl.appendChild(newLi);

                        // Ricorsione
                        recursivelyLoadSubmenu(newLi, newPage);
                    });

                    attachSubmenuListeners(submenuUl);
                } else {
                    parentLi.classList.remove("has-submenu");
                    if (submenuUl) submenuUl.remove();
                }
            })
            .catch(err => {
                console.error(`Error in recursive loading of ${pageFile}: ${err}`);
                parentLi.classList.remove("has-submenu");
            });
    }

    function removeDuplicateMenuItems() {
        const seenPages = new Set();
        const allMenuItems = menuList.querySelectorAll("li[data-page]");
        allMenuItems.forEach(li => {
            const pagePath = li.getAttribute("data-page");
            if (seenPages.has(pagePath)) li.remove();
            else seenPages.add(pagePath);
        });
    }

    // ======================= FOOTER NAVIGATION =======================
    const prevBtn = document.getElementById("prev-page");
    const nextBtn = document.getElementById("next-page");

    function getMenuPages() {
        return Array.from(menuList.querySelectorAll("li[data-page]"))
            .map(li => li.getAttribute("data-page"));
    }

    function updateFooterButtons(currentPage) {
        const pages = getMenuPages();
        const index = pages.indexOf(currentPage);

        if (!prevBtn || !nextBtn) return; // evita errori se footer non esiste

        prevBtn.disabled = index <= 0;
        nextBtn.disabled = index === -1 || index >= pages.length - 1;

        prevBtn.onclick = () => {
            if (index > 0) {
                const prevPage = pages[index - 1];
                const li = menuList.querySelector(`li[data-page="${prevPage}"]`);
                loadPage(prevPage, li);
            }
        };

        nextBtn.onclick = () => {
            if (index < pages.length - 1) {
                const nextPage = pages[index + 1];
                const li = menuList.querySelector(`li[data-page="${nextPage}"]`);
                loadPage(nextPage, li);
            }
        };
    }

    // ======================= Caricamento pagina =======================
    function loadPage(page, liToActivate = null) {
        menu.querySelectorAll("li[data-page].active").forEach(item => item.classList.remove("active"));

        if (!liToActivate) liToActivate = menu.querySelector(`li[data-page="${page}"]`);

        if (liToActivate) {
            liToActivate.classList.add("active");
            openMenuToLi(liToActivate);
            closeAllSubmenus(liToActivate);
        }

        const pageContentDiv = document.getElementById("page-content");

        fetch(page)
            .then(r => (r.ok ? r.text() : Promise.reject(`Page not found: ${page}`)))
            .then(html => {
                pageContentDiv.innerHTML = html; 

                const meta = pageDiv.querySelector('meta[name="image-basepath"]');
                const basePath = meta ? meta.content : "";
                setImagePaths(basePath, pageDiv);

                attachPageInternalLinks();

                // ✅ aggiorna il footer dopo ogni caricamento
                updateFooterButtons(page);
            })
            .catch(err => {
                pageDiv.innerHTML = `<p style="color:red;">Error loading ${page}: ${err}</p>`;
                updateFooterButtons(page);
            });
    }

    // ======================= INITIALIZATION =======================
    const initialMenuItems = menuList.querySelectorAll("li[data-page]");

    initialMenuItems.forEach(li => {
        const page = li.getAttribute("data-page");

        const originalText = li.textContent.trim();
        li.textContent = '';
        const contentWrapper = document.createElement("span");
        contentWrapper.classList.add("menu-title-content");
        contentWrapper.textContent = originalText;
        li.insertBefore(contentWrapper, li.firstChild);

        let submenu = li.querySelector(".submenu");
        if (!submenu) {
            submenu = document.createElement("ul");
            submenu.classList.add("submenu");
            li.appendChild(submenu);
        }

        recursivelyLoadSubmenu(li, page);
    });

    setTimeout(removeDuplicateMenuItems, 1000);
    attachSubmenuListeners(menuList);

    const initialPageLi = menuList.querySelector("li[data-page]");
    if (initialPageLi) {
        loadPage(initialPageLi.getAttribute("data-page"), initialPageLi);
    }
});
