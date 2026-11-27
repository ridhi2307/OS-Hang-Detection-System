(() => {
    const key = "os-guardian.theme";
    const preference = matchMedia("(prefers-color-scheme: dark)");
    let choice = "dark";
    try {
        const stored = localStorage.getItem(key);
        if (stored === "dark" || stored === "light" || stored === "system") choice = stored;
    } catch { /* Preferences can still change for this visit. */ }

    function apply() {
        const theme = choice === "system" ? (preference.matches ? "dark" : "light") : choice;
        document.documentElement.dataset.theme = theme;
        document.dispatchEvent(new Event("guardian-theme"));
    }

    apply();
    preference.addEventListener("change", () => {
        if (choice === "system") apply();
    });
    document.addEventListener("DOMContentLoaded", () => {
        const select = document.getElementById("themeChoice");
        select.value = choice;
        select.addEventListener("change", () => {
            choice = select.value;
            try { localStorage.setItem(key, choice); } catch { /* Storage is optional. */ }
            apply();
        });
    });
})();
