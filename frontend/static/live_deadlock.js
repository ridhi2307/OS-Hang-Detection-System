(() => {
    const panel = document.getElementById("liveDemo");
    const status = document.getElementById("demoStatus");
    const timer = document.getElementById("demoTimer");
    const table = document.getElementById("demoWorkers");
    const messages = {
        idle: "Start the workers to see their Windows process IDs.",
        starting: "The two workers are acquiring their first locks.",
        ready: "Both jobs hold one lock. Request the second locks to create a circular wait.",
        requesting: "Both workers have been asked to acquire the other lock.",
        circular_wait: "Circular wait detected: Print job → Archive job → Print job. Roll back the archive job to release its lock.",
        recovering: "The archive job is releasing its lock so the print job can finish.",
        resolved: "Recovered. The archive job rolled back, the print job finished, and both workers exited.",
        expired: "The time limit ended the experiment. Both workers exited and their locks were released.",
        failed: "A worker exited unexpectedly. Both workers have now stopped."
    };
    let runId = null;
    let busy = false;
    let queued = null;
    function render(data) {
        runId = data.run_id;
        status.textContent = messages[data.phase];
        timer.textContent = data.workers.some(w => w.alive) ? `Automatic cleanup in ${data.seconds_left}s` : "";
        panel.querySelector('[data-action="start"]').disabled = !["idle","resolved","expired","failed"].includes(data.phase);
        panel.querySelector('[data-action="advance"]').disabled = data.phase !== "ready";
        panel.querySelector('[data-action="recover"]').disabled = data.phase !== "circular_wait";
        if (data.workers.length) {
            makeTable(table, ["Worker", "Local PID", "Holds", "Waiting for", "State"],
                data.workers.map(w => [w.name, w.pid, w.holds ?? "—", w.waits_for ?? "—", w.status]));
        } else table.replaceChildren();
    }
    async function refresh(action) {
        if (busy) {
            if (action) queued = action;
            return;
        }
        if (!action && (document.hidden || location.hash !== "#deadlock")) return;
        if (action) for (const button of panel.querySelectorAll("button")) button.disabled = true;
        busy = true;
        try {
            const options = action ? {method:"POST", headers:{"Content-Type":"application/json"},
                body:JSON.stringify({action, run_id:runId})} : {};
            const response = await fetch("/api/lab/live-deadlock", options);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Unable to update the demo.");
            render(data);
        } catch (error) {
            status.textContent = error.message;
        } finally {
            busy = false;
            if (queued) {
                const next = queued;
                queued = null;
                refresh(next);
            }
        }
    }
    for (const button of panel.querySelectorAll("button")) button.onclick = () => refresh(button.dataset.action);
    window.addEventListener("hashchange", () => refresh());
    setInterval(() => refresh(), 750);
    refresh();
})();
