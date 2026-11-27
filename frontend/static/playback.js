function playback(host, draw) {
    let index = 0, count = 0, clock;
    host.innerHTML = '<button type="button" data-k="previous">← Previous</button><output></output><button type="button" data-k="next">Next →</button><button type="button" data-k="play">Run automatically</button><button type="button" data-k="reset">Reset</button><label>Speed <select><option value="1200">1×</option><option value="600">2×</option><option value="300">4×</option></select></label>';
    const key = name => host.querySelector('[data-k="'+name+'"]');
    const speed = host.querySelector("select");
    function stop() {
        clearInterval(clock);
        clock = null;
        key("play").textContent = index > 0 && index < count-1 ? "Resume" : "Run automatically";
    }
    function render() {
        host.querySelector("output").textContent = `Step ${index+1} / ${count}`;
        key("previous").disabled = index === 0;
        key("next").disabled = index >= count-1;
        draw(index);
    }
    function play() {
        if (!count) return;
        if (index === count-1) index = 0;
        render();
        key("play").textContent = "Pause";
        clock = setInterval(() => {
            index = Math.min(index+1,count-1);
            if (index === count-1) stop();
            render();
        }, Number(speed.value));
    }
    key("play").onclick = () => clock ? stop() : play();
    key("previous").onclick = () => { index--; stop(); render(); };
    key("next").onclick = () => { index++; stop(); render(); };
    key("reset").onclick = () => { index=0; stop(); render(); };
    speed.onchange = () => { if (clock) {stop(); play();} };
    window.addEventListener("hashchange", stop);
    return {load(n,i=0) { count=n; index=i; stop(); render(); }, stop};
}
