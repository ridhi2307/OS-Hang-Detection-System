let pageRuns;
const pagesPlayer=playback(document.getElementById("pagePlayer"),i=>{
    const box=document.getElementById("pageFrames");box.replaceChildren();
    const rows=[];
    for(const [policy,run] of Object.entries(pageRuns)){
        const item=run.trace[i], card=document.createElement("div");card.className="frame-row";
        const title=document.createElement("strong");title.textContent=policy;card.append(title);
        for(const page of item.frames){ const f=document.createElement("span");f.textContent=page;card.append(f); }
        box.append(card);
        rows.push([policy,item.page,item.hit?"Hit":"Fault",item.evicted??"—",run.trace.slice(0,i+1).filter(t=>!t.hit).length]);
    }
    makeTable(document.getElementById("labTrace"),["Policy","Request","Decision","Evicted","Faults so far"],rows);
});
const labForm = document.getElementById("labForm");
labForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = labForm.querySelector("button");
    const summary = document.getElementById("labSummary");
    const trace = document.getElementById("labTrace");
    pagesPlayer.stop();
    document.getElementById("pagePlayer").hidden=true;
    document.getElementById("pageFrames").replaceChildren();
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
        pageRuns=data;
        summary.textContent=Object.entries(data).map(([k,r])=>k+" · "+r.hits+" hits / "+r.faults+" faults").join("   |   ");
        document.getElementById("pagePlayer").hidden=false;
        pagesPlayer.load(data.FIFO.trace.length);
    } catch (error) {
        summary.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});
