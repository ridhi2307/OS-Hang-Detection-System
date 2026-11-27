const workspaceLinks = Array.from(document.querySelectorAll(".sidebar nav a"));
function showWorkspace() {
    const link = workspaceLinks.find(item => item.hash === location.hash) || workspaceLinks[0];
    const page = link.hash.slice(1);
    for (const section of document.querySelectorAll("main > section")) {
        section.hidden = section.id !== page && !(page === "overview" && section.id === "charts");
    }
    for (const item of workspaceLinks) {
        item.classList.toggle("active", item === link);
        if (item === link) item.setAttribute("aria-current", "page");
        else item.removeAttribute("aria-current");
    }
    document.getElementById("pageTitle").textContent =
        page === "overview" ? "System overview" : document.querySelector("#" + page + " .section-title").textContent;
    window.scrollTo({top: 0, behavior: "instant"});
}
window.addEventListener("hashchange", showWorkspace);
showWorkspace();
