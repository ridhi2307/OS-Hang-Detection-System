function makeTable(container, columns, rows) {
    const table = document.createElement("table");
    const header = table.createTHead().insertRow();
    for (const title of columns) {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = title;
        header.append(th);
    }
    const body = table.createTBody();
    for (const values of rows) {
        const row = body.insertRow();
        for (const value of values) row.insertCell().textContent = value;
    }
    container.replaceChildren(table);
}

for (const lab of document.querySelectorAll(".resource-lab")) {
    const find = selector => lab.querySelector(selector);
    const form = find("form");
    const policy = find(".policy");
    let result, inputs, step;
    const player = playback(find(".playback"), showStep);
    function showStep(index) {
        step = index;
        const run = result.runs[policy.selectedIndex];
        const values = run.steps[step];
        const visual = find(".step-visual");
        visual.replaceChildren();
        if (lab.id === "disk") {
            const caption = document.createElement("p");
            caption.textContent = "Head at cylinder "+values[1]+" · "+ run.steps.slice(0,step+1).map(s=>s[1]).join(" → ");
            const track = document.createElement("div"); track.className="disk-track";
            const head = document.createElement("i"); head.style.left=(values[1]/199*100)+"%";
            if (!matchMedia("(prefers-reduced-motion: reduce)").matches)
                head.animate([{left:(values[0]/199*100)+"%"},{left:head.style.left}],{duration:260});
            track.append(head); visual.append(track,caption);
        }
        if (lab.id === "allocation") {
            const blocks = inputs.holes.trim().split(/[\s,]+/).map(Number);
            const free = values[2].split(" · ").map(Number);
            free.forEach((n,i)=>{
                const block=document.createElement("div"); block.className="block-meter";
                const bar=document.createElement("progress"); bar.max=blocks[i]; bar.value=blocks[i]-n;
                const placed=run.steps.slice(0,step+1).flatMap((s,j)=>s[1]==="Placed in B"+(i+1) ? ["P"+(j+1)+" ("+s[0]+")"] : []);
                block.append("B"+(i+1)+" · "+n+" free",bar,placed.join(" · ") || "Empty"); visual.append(block);
            });
            const info=document.createElement("p");
            info.textContent="Split-block model · internal fragmentation 0 units · free outside largest hole "+(values[3]-Math.max(...free))+" units.";
            visual.append(info);
        }
        makeTable(find(".trace"), result.columns, [values]);
        Array.from(find(".timeline").children).forEach((item, i) => item.classList.toggle("selected", i === step));
    }
    function showPolicy() {
        step = 0;
        const timeline = find(".timeline");
        timeline.replaceChildren();
        timeline.hidden = lab.id !== "cpu";
        if (!timeline.hidden) {
            result.runs[policy.selectedIndex].steps.forEach(([start, end, job], i) => {
                const segment = document.createElement("button");
                segment.type = "button";
                segment.textContent = job;
                segment.title = `${job} · ticks ${start}–${end}`;
                segment.setAttribute("aria-label", segment.title);
                segment.style.flexGrow = end - start;
                segment.onclick = () => player.load(result.runs[policy.selectedIndex].steps.length,i);
                timeline.append(segment);
            });
        }
        const run = result.runs[policy.selectedIndex];
        if (run.jobs) makeTable(find(".job-details"),["Process","Arrival","Burst","Priority","Completion","Wait","Turnaround","Response"],run.jobs);
        player.load(run.steps.length);
    }
    form.querySelector(".preset").onchange = event => {
        const values = JSON.parse(event.target.value);
        form.querySelectorAll("input").forEach((input, i) => { input.value = values[i]; });
    };
    form.oninput = form.onchange = () => {
        player.stop();
        find(".lab-results").hidden = true;
        find(".feedback").textContent = "Run the comparison to analyze this workload.";
    };
    form.onsubmit = async event => {
        event.preventDefault();
        inputs = Object.fromEntries(new FormData(form));
        find(".lab-results").hidden = true;
        find(".feedback").textContent = "Running comparison…";
        for (const el of form.elements) el.disabled = true;
        try {
            const response = await fetch("/api/lab/" + lab.id, {
                method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(inputs)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Comparison failed.");
            result = data;
            makeTable(find(".comparison"), ["Policy", ...result.metrics], result.runs.map(run => [run.name, ...run.metrics]));
            policy.replaceChildren(...result.runs.map(run => new Option(run.name)));
            find(".lab-results").hidden = false;
            showPolicy();
            const scores = result.runs.map(run => run.metrics[0]);
            const best = lab.id === "allocation" ? Math.max(...scores) : Math.min(...scores);
            const leaders = result.runs.filter(run => run.metrics[0] === best).map(run => run.name);
            const criterion = {cpu:"Lowest mean wait", disk:"Least head travel", allocation:"Most requests placed"}[lab.id];
            find(".feedback").textContent = `${criterion} on this workload: ${leaders.join(" and ")} (${best}).`;
        } catch (error) {
            find(".feedback").textContent = error.message;
        } finally {
            for (const el of form.elements) el.disabled = false;
        }
    };
    policy.onchange = showPolicy;
    find(".export").onclick = () => {
        const rows = [["Workload", lab.id], ...Object.entries(inputs), [], ["Policy", ...result.metrics],
            ...result.runs.map(run => [run.name, ...run.metrics]), [], ["Policy", "Step", ...result.columns]];
        for (const run of result.runs) run.steps.forEach((row, i) => rows.push([run.name, i + 1, ...row]));
        const csv = rows.map(row => row.map(value => '"' + String(value).replaceAll('"', '""') + '"').join(",")).join("\r\n");
        const url = URL.createObjectURL(new Blob([csv], {type:"text/csv;charset=utf-8"}));
        const link = document.createElement("a");
        link.href = url;
        link.download = "os-guardian-" + lab.id + ".csv";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
}
