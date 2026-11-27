const navPaths={
overview:"M3 10 12 3l9 7v10h-6v-6H9v6H3z", health:"M2 12h5l3-8 4 16 3-8h5",
processes:"M4 5h16M4 12h16M4 19h16", hangs:"M3 4h18v15H3z M3 8h18 M6 14h3l2-3 3 5 2-3h2",
memory:"M3 7h18v10H3z M6 10v3m4-3v3m4-3v3m4-3v3 M6 17v3m4-3v3m4-3v3m4-3v3",
storage:"M5 5h14l3 11v3H2v-3z M3 15h18m-5 2h2", recovery:"M4 5v6h6 M4 11a8 8 0 1 1 1 7",
cpu:"M6 6h12v12H6z M9 2v4m5-4v4M9 18v4m5-4v4M2 9h4m-4 5h4m12-5h4m-4 5h4",
disk:"M12 3a9 9 0 1 0 .1 0 M12 10a2 2 0 1 0 .1 0 M14 10l5-5",
allocation:"M3 4h18v16H3z M3 10h18m-12 0v10",lab:"M3 6h12m-3-3 3 3-3 3 M21 18H9m3-3-3 3 3 3",
deadlock:"M5 10h14v11H5z M8 10V7a4 4 0 0 1 8 0v3"};
for(const link of document.querySelectorAll(".sidebar nav a")){
 const path=navPaths[link.hash.slice(1)];
 if(path) link.insertAdjacentHTML("afterbegin",`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`);
}
