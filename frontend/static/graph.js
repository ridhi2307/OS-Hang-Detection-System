(() => {
    const id = name => document.getElementById(name);
    const presets = JSON.parse(id("scenarioData").textContent);
    const selector = id("graphScenario"), custom = id("graphJson");
    let frames, scenario, victims=[];
    const timeline = playback(id("graphLab").querySelector(".playback"), render);
    function editMatrix(spec) {
        const processes=spec.allocation.length, resources=spec.capacity.length;
        id("graphProcesses").value=processes; id("graphResources").value=resources;
        const box=id("matrixEditor"); box.replaceChildren();
        const table=document.createElement("table"), header=table.createTHead().insertRow();
        for(const name of ["State",...spec.capacity.map((_,j)=>"R"+(j+1))]){
            const th=document.createElement("th");th.textContent=name;header.append(th);
        }
        const body=table.createTBody();
        function row(title,vector) {
            const line=body.insertRow();line.insertCell().textContent=title;
            vector.forEach((v,j)=>{
                const input=document.createElement("input");input.type="number";
                input.min=title==="Capacity"?"1":"0";input.max="16";input.value=v;
                input.setAttribute("aria-label",title+" R"+(j+1));
                input.oninput=()=>{
                    vector[j]=input.value===""?null:Number(input.value);
                    custom.value=JSON.stringify(spec,null,2);
                    timeline.stop();id("graphOutput").hidden=true;
                };
                line.insertCell().append(input);
            });
        }
        row("Capacity",spec.capacity);
        spec.allocation.forEach((vector,i)=>{row("P"+(i+1)+" holds",vector);row("P"+(i+1)+" requests",spec.requests[i]);});
        box.append(table);
        custom.value=JSON.stringify(spec,null,2);
    }
    function resizeMatrix() {
        const p=Number(id("graphProcesses").value),r=Number(id("graphResources").value);
        if (!Number.isInteger(p)||!Number.isInteger(r)||p<1||p>8||r<1||r>6) return;
        let before;
        try {before=JSON.parse(custom.value);} catch {before={};}
        const vector=(old,fill)=>Array.from({length:r},(_,j)=>old?.[j]??fill);
        const matrix=key=>Array.from({length:p},(_,i)=>vector(before[key]?.[i],0));
        editMatrix({capacity:vector(before.capacity,1),allocation:matrix("allocation"),requests:matrix("requests")});
        timeline.stop();id("graphOutput").hidden=true;
    }
    id("graphProcesses").onchange=resizeMatrix;id("graphResources").onchange=resizeMatrix;
    id("applyGraphJson").onclick=async()=>{
        const error=id("graphLab").querySelector(".graph-error");
        try {
            const spec=JSON.parse(custom.value);
            const r=await fetch("/api/lab/graph",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scenario:spec})});
            if(!r.ok) throw Error((await r.json()).error);
            editMatrix(spec);error.textContent="";
        } catch(e){error.textContent=e.message;}
    };
    function setup() {
        timeline.stop(); victims=[];
        id("graphOutput").hidden = true;
        const editable = selector.value === "Custom scenario";
        id("customGraph").hidden = !editable;
        const spec=presets[selector.value] || presets["Two-process deadlock"];
        if(editable) editMatrix(structuredClone(spec));
        else custom.value=JSON.stringify(spec,null,2);
    }
    function render(i) {
        const f = frames[i], count = Math.max(f.held.length,f.available.length);
        const svg = id("allocationGraph"), height = Math.max(190,count*68+35);
        svg.setAttribute("viewBox",`0 0 490 ${height}`);
        const y = n => 44+n*66;
        let edges = "", nodes = "";
        const markers = ["owns","needs"].map(s => `<marker id="${s}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="${s}" d="M0 0L10 5L0 10Z"/></marker>`).join("");
        for (const [p,row] of f.held.entries()) {
            const cls = f.finished.includes(p) ? "finished" : f.deadlocked.includes(p) ? "blocked" : f.requests[p].some(Boolean) ? "waiting" : "running";
            nodes += `<g class="${cls}"><circle cx="68" cy="${y(p)}" r="24"/><text x="68" y="${y(p)+5}">P${p+1}</text></g>`;
            row.forEach((units,r) => {
                if (units) edges += `<path class="edge owns" d="M370 ${y(r)-5} L94 ${y(p)-5}" marker-end="url(#owns)"/><text x="310" y="${y(r)+(y(p)-y(r))*.23-10}">×${units}</text>`;
                if (f.requests[p][r]) edges += `<path class="edge needs" d="M94 ${y(p)+6} L370 ${y(r)+6}" marker-end="url(#needs)"/><text x="155" y="${y(p)+(y(r)-y(p))*.22+21}">×${f.requests[p][r]}</text>`;
            });
        }
        f.available.forEach((v,r) => {nodes += `<g class="${v===scenario.capacity[r]?"available":"allocated"}"><rect x="373" y="${y(r)-23}" width="111" height="46" rx="10"/><text x="429" y="${y(r)+5}">R${r+1} · ${v} free</text></g>`;});
        svg.innerHTML = "<defs>"+markers+"</defs>"+edges+nodes;
        id("graphText").textContent = f.text;
        id("graphWhy").textContent = f.deadlocked.length ? "Outstanding requests exceed the available instances even after every process that can finish releases its resources. Blocked holders: "+f.deadlocked.map(p=>"P"+(p+1)).join(", ") : "The current outstanding requests admit a completion order.";
        const canRecover = i===frames.length-1 && f.deadlocked.length>0;
        id("graphLab").querySelector(".graph-recover").hidden = !canRecover;
        if (canRecover) id("graphVictim").replaceChildren(...f.deadlocked.map(p=>new Option("P"+(p+1),p)));
    }
    async function run(recover) {
        const error = id("graphLab").querySelector(".graph-error");
        try {
            timeline.stop();
            const spec = JSON.parse(custom.value);
            const releases=recover ? [...victims,Number(id("graphVictim").value)] : [];
            const r = await fetch("/api/lab/graph",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scenario:spec,victim:releases})});
            const data=await r.json();
            if (!r.ok) throw Error(data.error);
            const start= recover ? frames.length : 0;
            scenario=spec; victims=releases; frames=data.steps;
            id("graphOutput").hidden=false;
            timeline.load(frames.length,start);
            error.textContent="";
        } catch(e) { error.textContent=e.message; }
    }
    selector.onchange=setup; custom.oninput=()=>{ timeline.stop(); id("graphOutput").hidden=true; };
    id("graphStart").onclick=()=>run(false); id("graphRecover").onclick=()=>run(true);
    setup();
})();
