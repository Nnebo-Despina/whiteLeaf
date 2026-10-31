// Shared nav behaviour (mirrors NavBar.jsx)
(function () {
  var header = document.querySelector("[data-nav]");
  var logo = document.querySelector("[data-nav-logo]");
  var links = document.querySelector("[data-nav-links]");
  var btn = document.querySelector("[data-nav-btn]");
  var menu = document.getElementById("mobile-menu");

  // Overlay pages (Home, About): transparent at top, cream + blur after 24px of scroll
  if (header && header.dataset.nav === "overlay") {
    var swap = function (el, off, on, scrolled) {
      if (!el) return;
      el.classList.remove.apply(el.classList, scrolled ? off : on);
      el.classList.add.apply(el.classList, scrolled ? on : off);
    };
    var update = function () {
      var s = window.scrollY > 24;
      swap(header, ["bg-transparent"], ["bg-[#FAF6EE]/95", "backdrop-blur"], s);
      swap(logo, ["text-white"], ["text-[#16302A]"], s);
      swap(links, ["text-white/90"], ["text-[#3a352c]"], s);
      swap(btn, ["text-white"], ["text-[#16302A]"], s);
    };
    window.addEventListener("scroll", update);
    update();
  }

  // Mobile menu toggle
  if (btn && menu) {
    btn.addEventListener("click", function () {
      var nowOpen = menu.classList.toggle("hidden") === false;
      menu.classList.toggle("flex", nowOpen);
      var icon = document.getElementById("menu-icon");
      var next = document.createElement("i");
      next.id = "menu-icon";
      next.className = "w-6 h-6";
      next.setAttribute("data-lucide", nowOpen ? "x" : "menu");
      icon.replaceWith(next);
      lucide.createIcons();
    });
    menu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { menu.classList.add("hidden"); menu.classList.remove("flex"); });
    });
  }
})();
