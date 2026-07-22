// EasyEquities portfolio widget for Übersicht.
// Installed by ../setup.sh, which substitutes __DATA_DIR__ with the repo path.
// Reads value.json + config.json every 60s. Honors config.theme (auto/light/dark).

const DATA_DIR = "__DATA_DIR__";

export const command =
  `cat "${DATA_DIR}/value.json" 2>/dev/null || echo '{}'; ` +
  `echo '@@@EE@@@'; ` +
  `cat "${DATA_DIR}/config.json" 2>/dev/null || echo '{}'`;

export const refreshFrequency = 60000;

const num = (n) => Number(n || 0).toLocaleString("en-ZA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const palette = (dark) => dark
  ? { bg:"#161618", border:"#2b2b2e", text:"#f2f2f0", muted:"#9a9aa0", faint:"#7c7c82",
      divider:"#2b2b2e", upBg:"rgba(45,201,150,.15)", upFg:"#3ddc9a", downBg:"rgba(229,72,77,.15)", downFg:"#ff6b6b" }
  : { bg:"#ffffff", border:"#e7e7e4", text:"#161615", muted:"#77776f", faint:"#a2a29b",
      divider:"#efefec", upBg:"#e1f5ee", upFg:"#0f6e56", downBg:"#fdecec", downFg:"#b3261e" };

const inRange = (series, range) => {
  if (range === "lifetime" || !series || series.length < 2) return series || [];
  const days = { "1Y":366, "1M":31, "1W":7 }[range] || 1e9;
  const last = new Date(series[series.length-1].date);
  const cut = new Date(last); cut.setDate(cut.getDate()-days);
  const f = series.filter((p) => new Date(p.date) >= cut);
  return f.length >= 2 ? f : series.slice(-2);
};

const chartPath = (series, W, H, pad) => {
  const pts = series || [];
  if (pts.length === 0) return { line:"", area:"", up:true };
  const vals = pts.map((p) => p.value);
  let mn = Math.min(...vals), mx = Math.max(...vals);
  if (mn === mx) { mn -= 1; mx += 1; }
  const y = (v) => pad + (H - 2*pad) * (1 - (v - mn) / (mx - mn));
  const x = (i) => (pts.length < 2 ? W/2 : (i/(pts.length-1))*W);
  const d = pts.length < 2
    ? `M0,${y(pts[0].value).toFixed(1)} L${W},${y(pts[0].value).toFixed(1)}`
    : pts.map((p,i) => (i?"L":"M") + x(i).toFixed(1) + "," + y(p.value).toFixed(1)).join(" ");
  const up = pts.length < 2 || pts[pts.length-1].value >= pts[0].value;
  return { line:d, area:d + ` L${W},${H} L0,${H} Z`, up };
};

export const className = `top:40px; left:40px; width:360px;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text",sans-serif;`;

export const render = ({ output }) => {
  const [rawV, rawC] = String(output).split("@@@EE@@@");
  let d = {}, cfg = {};
  try { d = JSON.parse(rawV); } catch (e) {}
  try { cfg = JSON.parse(rawC); } catch (e) {}

  const theme = cfg.theme || "auto";
  const dark = theme === "dark" ||
    (theme === "auto" && typeof window !== "undefined" && window.matchMedia &&
     window.matchMedia("(prefers-color-scheme: dark)").matches);
  const c = palette(dark);
  const sym = d.currency_symbol || cfg.currency_symbol || "R";
  const range = cfg.chart_range || "lifetime";
  const shown = cfg.accounts_shown || 2;

  const series = inRange(d.series, range);
  const { line, area, up } = chartPath(series, 320, 84, 8);
  const stroke = up ? "#16a06f" : "#e5484d";

  const dz = d.day_change, hasChange = dz !== null && dz !== undefined;
  const gain = hasChange && dz >= 0;
  const pillC = !hasChange || dz === 0 ? { background:c.divider, color:c.muted }
    : gain ? { background:c.upBg, color:c.upFg } : { background:c.downBg, color:c.downFg };
  const sign = gain ? "+" : "−";
  const sparse = !d.series || d.series.length < 2;

  const accounts = [...(d.accounts || [])].sort((a,b) => (b.value||0)-(a.value||0))
    .slice(0, shown >= 99 ? undefined : shown);

  return (
    <div style={{ background:c.bg, color:c.text, border:`1px solid ${c.border}`,
      borderRadius:18, padding:20, boxShadow:"0 10px 30px rgba(0,0,0,.28)" }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
        <b style={{ fontWeight:500, fontSize:15 }}>EasyEquities</b>
        <span style={{ fontSize:11, color:c.faint }}>Portfolio value</span>
      </div>
      <div style={{ display:"flex", alignItems:"baseline", gap:11, flexWrap:"wrap" }}>
        <div style={{ fontSize:33, fontWeight:500, letterSpacing:"-.5px", fontVariantNumeric:"tabular-nums" }}>
          <span style={{ fontSize:18, color:c.faint, marginRight:2 }}>{sym}</span>{num(d.total)}</div>
        <span style={{ ...pillC, display:"inline-flex", alignItems:"center", gap:4, fontSize:12,
          fontWeight:500, padding:"4px 9px", borderRadius:20 }}>
          {hasChange
            ? `${gain ? "▲" : "▼"} ${sign}${sym}${num(Math.abs(dz))}` +
              (d.day_change_pct !== null ? ` · ${sign}${Math.abs(d.day_change_pct).toFixed(2)}%` : "") + " today"
            : "— today"}
        </span>
      </div>
      <svg viewBox="0 0 320 90" width="100%" height="84" preserveAspectRatio="none" style={{ display:"block", margin:"14px 0 4px" }}>
        <defs>
          <linearGradient id="eeup" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#16a06f" stopOpacity=".22" /><stop offset="1" stopColor="#16a06f" stopOpacity="0" /></linearGradient>
          <linearGradient id="eedn" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#e5484d" stopOpacity=".22" /><stop offset="1" stopColor="#e5484d" stopOpacity="0" /></linearGradient>
        </defs>
        <path d={area} fill={up ? "url(#eeup)" : "url(#eedn)"} />
        <path d={line} fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {sparse ? <div style={{ fontSize:11, color:c.faint, textAlign:"center", margin:"6px 0" }}>
        collecting history — chart fills in daily</div> : null}
      <div style={{ borderTop:`1px solid ${c.divider}`, paddingTop:12, marginTop:12, display:"flex", flexDirection:"column", gap:7 }}>
        {accounts.map((a) => (
          <div key={a.id} style={{ display:"flex", justifyContent:"space-between", fontSize:13 }}>
            <span style={{ color:c.muted }}>{a.label}</span>
            <span style={{ fontVariantNumeric:"tabular-nums" }}>{sym}{num(a.value)}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop:12, fontSize:10, color:c.faint }}>source: {d.source || "—"} · as of {d.as_of || "—"}</div>
    </div>
  );
};
