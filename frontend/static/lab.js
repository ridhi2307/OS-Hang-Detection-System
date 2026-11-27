const labForm = document.getElementById("labForm");
labForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = labForm.querySelector("button");
    const summary = document.getElementById("labSummary");
    const trace = document.getElementById("labTrace");
    button.disabled = true;
    trace.replaceChildren();
    summary.textContent = "Comparing policies…";
    try {
        const response = await fetch("/api/lab/paging", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({pages: labForm.pages.value, frames: Number(labForm.frames.value)})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not run the simulation.");
        const {FIFO, LRU} = data;
        const gap = FIFO.faults - LRU.faults;
        const finding = gap === 0 ? "Both policies had the same number of faults." :
            `${gap > 0 ? "LRU" : "FIFO"} avoided ${Math.abs(gap)} page fault(s) on this sequence.`;
        summary.textContent = `FIFO · ${FIFO.faults} faults / ${FIFO.hits} hits. LRU · ${LRU.faults} faults / ${LRU.hits} hits. ${finding}`;
        const table = document.createElement("table");
        table.innerHTML = "<thead><tr><th>Step</th><th>Request</th><th>FIFO frames</th><th>FIFO decision</th><th>LRU frames</th><th>LRU decision</th></tr></thead>";
        const body = table.createTBody();
        FIFO.trace.forEach((step, i) => {
            const row = body.insertRow();
            row.insertCell().textContent = i + 1;
            row.insertCell().textContent = step.page;
            for (const item of [step, LRU.trace[i]]) {
                row.insertCell().textContent = item.frames.join(" · ");
                const decision = row.insertCell();
                decision.textContent = item.hit ? "Hit" : item.evicted === null ? "Fault · free frame" : `Fault · evict ${item.evicted}`;
                decision.className = item.hit ? "status-normal" : "status-warning";
            }
        });
        trace.append(table);
    } catch (error) {
        summary.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});
