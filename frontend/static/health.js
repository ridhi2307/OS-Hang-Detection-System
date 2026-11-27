let snapshot, trend;
const byId = id => document.getElementById(id);
const stamp = t => t ? new Date(t*1000).toLocaleString() : "—";
function healthTable(id, columns, rows, empty) {
    const box=byId(id);
    if (!rows.length) { box.textContent=empty; return; }
    makeTable(box,columns,rows);
    for (const cell of box.querySelectorAll("td")) {
        if (["Healthy","RESPONDING","Restart verified","Responsive again"].includes(cell.textContent)) cell.className="status-normal";
        if (["Unresponsive","NOT RESPONDING","Failed","Hang detected"].includes(cell.textContent)) cell.className="status-danger";
        if (["Checking","Recovering","Unknown"].includes(cell.textContent)) cell.className="status-warning";
    }
}
function renderApplications() {
    const health=snapshot.health;
    const metrics=new Map(snapshot.processes.data.map(p=>[p.pid,p]));
    const rows=health.apps.filter(a=>byId("appFilter").value==="All" || byId("appFilter").value===a.state);
    healthTable("applicationRows",["Application","PID","CPU %","Memory MB","State","Windows probe","First stalled","Duration","Checked"],
        rows.map(a=>[a.process_name,a.pid,metrics.get(a.pid)?.cpu_percent??"—",metrics.get(a.pid)?.memory_mb??"—",a.state,a.status,
            stamp(a.since),a.since?Math.floor(a.checked-a.since)+"s":"—",stamp(a.checked)]),"No matching visible applications.");
}
function renderProcesses() {
    const query=byId("processSearch").value.toLowerCase(), sort=byId("processSort").value;
    const apps=new Map(snapshot.health.apps.map(a=>[a.pid,a]));
    let rows=snapshot.processes.data.filter(p=>(p.name+" "+p.pid).toLowerCase().includes(query));
    if (byId("processScope").value==="apps") rows=rows.filter(p=>apps.has(p.pid));
    rows.sort((a,b)=>sort==="name"?a.name.localeCompare(b.name):b[sort]-a[sort]);
    healthTable("processRows",["Process","PID","CPU %","Memory MB","Process status","App health","Started"],
        rows.map(p=>[p.name,p.pid,p.cpu_percent,p.memory_mb,p.status,apps.get(p.pid)?.state??"No monitored window",stamp(p.started)]),"No matching processes.");
    byId("processRows").querySelectorAll("tbody tr").forEach((row,i)=>{
        const p=rows[i],btn=document.createElement("button");
        btn.textContent=p.name;btn.className="process-link";
        btn.onclick=()=>{
            const windows=snapshot.health.windows.filter(w=>w.pid===p.pid);
            const info=byId("processInfo");info.replaceChildren();
            const heading=document.createElement("p");
            heading.textContent=p.name+" · PID "+p.pid+" · started "+stamp(p.started);
            const resources=document.createElement("p");
            resources.textContent=p.cpu_percent+"% CPU · "+p.memory_mb+" MB resident memory · "+p.status;
            const details=document.createElement("p");
            details.textContent=windows.length ? windows.map(w=>w.window_title+" ("+w.status+")").join(" · ") : "No visible titled application windows in this sample.";
            info.append(heading,resources,details);byId("processDetails").showModal();
        };
        row.cells[0].replaceChildren(btn);
    });
}
function renderHealth(data) {
    snapshot=data;
    const h=data.health,c=h.counts;
    for (const [key,value] of Object.entries({total:h.apps.length,healthy:c.Healthy,hung:c.Unresponsive+c.Failed,recovering:c.Recovering,success:h.successes})) byId("kpi-"+key).textContent=value;
    const stalled=c.Unresponsive+c.Failed;
    byId("healthHeadline").textContent=stalled ? `${stalled} application${stalled===1?" needs":"s need"} attention` : "No confirmed hangs";
    byId("healthDescription").textContent=`${h.apps.length} visible applications · ${c.Checking} awaiting confirmation · ${c.Unknown} inconclusive`;
    byId("memoryGauge").value=data.memory.system.usage_percent;
    byId("memoryGaugeCaption").textContent=data.memory.system.used_gb+" GB used · "+data.memory.system.available_gb+" GB available";
    const disk=data.storage.reduce((a,d)=>[a[0]+d.used_gb,a[1]+d.total_gb],[0,0]);
    byId("systemSummary").textContent=`CPU  ${data.cpu}%     •     RAM  ${data.memory.system.usage_percent}%     •     Disk space used  ${disk[1]?(100*disk[0]/disk[1]).toFixed(1)+"%":"—"}     •     Running processes  ${data.running}`;
    if (document.activeElement!==byId("thresholdInput")) byId("thresholdInput").value=h.threshold;
    renderApplications(); renderProcesses();
    healthTable("windowRows",["Window title","Application","PID","Windows probe","Confirmation","Checked"],
        h.windows.map(w=>[w.window_title,w.process_name,w.pid,w.status,w.state,stamp(w.checked)]),"No titled windows visible to this session.");
    const eventRows=h.events.map(e=>[stamp(e.at),e.name,e.pid,e.event,e.detail]);
    healthTable("incidentHistory",["Time","Application","PID","Event","Details"],eventRows.filter(row=>["Hang detected","Window gone","Responsive again"].includes(row[3])),"No detection events recorded.");
    healthTable("recoveryLog",["Time","Application","PID","Event","Result / reason"],eventRows,"No events recorded.");
    const feed=byId("activityFeed"); feed.replaceChildren();
    for (const e of h.events.slice(0,3)) {
        const line=document.createElement("p"), title=document.createElement("strong"), sub=document.createElement("small");
        title.textContent=e.event; sub.textContent=e.name+" · "+stamp(e.at);
        line.append(title,sub); feed.append(line);
    }
    if (!feed.children.length) feed.textContent="No hang or recovery events recorded.";
    byId("recoveryIncidents").replaceChildren();
    for(const a of h.apps.filter(a=>a.incident)) {
        const card=document.createElement("article"); card.className="incident-card";
        const title=document.createElement("h4"); title.textContent=`${a.process_name} · PID ${a.pid} · ${a.state}`;
        const info=document.createElement("p");
        const proc=data.processes.data.find(p=>p.pid===a.pid);
        const evidence=proc && proc.cpu_percent>=80 ? "Elevated process CPU may contribute." : data.memory.system.usage_percent>=90 ? "High system memory pressure may contribute." : "The root cause is undetermined.";
        info.textContent="Windows reported a stalled UI thread. "+evidence+" "+(a.supported?"Confirmed actions are available for this test app.":"Recheck this application or wait for its message loop to resume.");
        card.append(title,info);
        if(a.supported && a.state!=="Recovering") for(const method of ["restart","end"]) {
            const btn=document.createElement("button"); btn.textContent=method==="restart"?"Restart test application":"End test application";
            btn.onclick=async()=>{
                if(!confirm(`${btn.textContent} (PID ${a.pid})? Unsaved work in this test application will be lost.`)) return;
                btn.disabled=true;
                try {
                    const r=await fetch("/api/recovery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({confirmed:true,method,incident:a.incident,pid:a.pid})});
                    const result=await r.json(); byId("actionResult").textContent=result.message;
                } catch(e) { byId("actionResult").textContent=e.message; }
                finally {btn.disabled=false; await loadDashboard();}
            };
            card.append(btn);
        }
        byId("recoveryIncidents").append(card);
    }
    if(!byId("recoveryIncidents").children.length) byId("recoveryIncidents").textContent="No active recovery incidents.";
    const series=h.history;
    if(!trend) trend=new Chart(byId("healthChart"),{type:"line",data:{labels:[],datasets:[
        {label:"Healthy",borderColor:"#24beab",data:[],pointRadius:1},{label:"Unresponsive",borderColor:"#ff9569",data:[],pointRadius:2},{label:"New hangs",borderColor:"#aa83fa",data:[],borderDash:[3,3],pointRadius:1}]},
        options:{responsive:true,maintainAspectRatio:false,animation:false,scales:{y:{beginAtZero:true,ticks:{precision:0}},x:{ticks:{maxTicksLimit:5}}}}});
    trend.data.labels=series.map(s=>new Date(s.at*1000).toLocaleTimeString());
    trend.data.datasets[0].data=series.map(s=>s.healthy);trend.data.datasets[1].data=series.map(s=>s.hung);trend.data.datasets[2].data=series.map(s=>s.detected);trend.update();
}
byId("appFilter").onchange=()=>snapshot&&renderApplications();
for(const id of ["processSearch","processSort","processScope"]) byId(id).oninput=()=>snapshot&&renderProcesses();
byId("thresholdForm").onsubmit=async e=>{
    e.preventDefault();
    try {
        const r=await fetch("/api/health/threshold",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({seconds:Number(byId("thresholdInput").value)})});
        byId("thresholdResult").textContent=r.ok?"Interval saved.":"Unable to save interval.";
    } catch(e){byId("thresholdResult").textContent=e.message;}
};
