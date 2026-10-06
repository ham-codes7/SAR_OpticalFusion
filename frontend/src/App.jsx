import { useEffect, useMemo, useState } from "react";
import MapView from "./MapView.jsx";

const PHENOMENA = {
  deforestation: { label: "Forest loss", noun: "forest loss", unit: "of forest loss detected" },
  urban: { label: "Urban growth", noun: "new built-up area", unit: "of new built-up area detected" },
};
const BASE_LAYERS = [
  ["optical", "Optical"],
  ["sar", "Radar"],
  ["fused", "Fused"],
];
const CLOUD_LEVELS = [0, 0.2, 0.4, 0.6];
const FUSION_VIEWS = [["ihs", "IHS"], ["pca", "PCA"], ["wavelet", "Wavelet"]];
const FUSED_VARIANTS = [["stack", "Band stack"], ["ihs", "IHS"], ["pca", "PCA"], ["wavelet", "Wavelet"]];
const STEPS = [
  "Finding Sentinel-1 and Sentinel-2 scenes",
  "Masking cloud and filtering radar speckle",
  "Aligning both sensors to one grid",
  "Fusing radar with optical",
  "Running the change detector on each input",
  "Scoring against reference land cover",
];
const MONTHS = "JFMAMJJASOND".split("");

const fmt = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-IN") : n.toFixed(1));
const km = (bbox) => {
  const [w, s, e, n] = bbox;
  const ns = (n - s) * 111;
  const ew = (e - w) * 111 * Math.cos(((s + n) / 2) * (Math.PI / 180));
  return `${ew.toFixed(0)} × ${ns.toFixed(0)} km`;
};

function shiftYears(iso, years) {
  const [y, m, d] = iso.split("-").map(Number);
  const leap = (yr) => (yr % 4 === 0 && yr % 100 !== 0) || yr % 400 === 0;
  const day = m === 2 && d === 29 && !leap(y + years) ? 28 : d;
  return `${y + years}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail || detail; } catch { /* keep default */ }
    throw new Error(detail);
  }
  return res.json();
}

export default function App() {
  const [config, setConfig] = useState(null);
  const [phenomenon, setPhenomenon] = useState("urban");
  const [presetId, setPresetId] = useState(null);
  const [area, setArea] = useState(null);
  const [polygon, setPolygon] = useState(null);
  const [drawing, setDrawing] = useState(null); // null | "rect" | "polygon"
  const [opacity, setOpacity] = useState(0.75);
  const [timeline, setTimeline] = useState(null); // { items: [{ year, result }], index, loading }
  const [dates, setDates] = useState(null);
  const [cloud, setCloud] = useState(0);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  const [base, setBase] = useState("optical");
  const [variant, setVariant] = useState("stack");
  const [fusedVariant, setFusedVariant] = useState("stack");
  const [overlay, setOverlay] = useState("detected"); // "detected" | "errors" | "off"
  const [collapsed, setCollapsed] = useState(false);
  const [cloudTest, setCloudTest] = useState(null); // { points: [{ cloud, result }], loading }
  const [split, setSplit] = useState(0.5);
  const [calendar, setCalendar] = useState(null);

  useEffect(() => {
    api("/api/config")
      .then((c) => {
        setConfig(c);
        setDates({ before: [...c.defaults.before], after: [...c.defaults.after] });
      })
      .catch((e) => setError(`Cannot reach the analysis server: ${e.message}`));
  }, []);

  useEffect(() => {
    if (!busy) return;
    setStep(0);
    const t = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 5500);
    return () => clearInterval(t);
  }, [busy]);

  const calendarKey = result ? `${result.bbox.join(",")}|${result.after.window[0].slice(0, 4)}` : null;
  useEffect(() => {
    if (!calendarKey) return;
    const [box, year] = calendarKey.split("|");
    const [w, s, e, n] = box.split(",");
    let stale = false;
    setCalendar(null);
    api(`/api/availability?west=${w}&south=${s}&east=${e}&north=${n}&year=${year}`).then((c) => !stale && setCalendar(c)).catch(() => {});
    return () => { stale = true; };
  }, [calendarKey]);

  const presets = useMemo(() => (config?.presets || []).filter((p) => p.phenomenon === phenomenon), [config, phenomenon]);

  function pickPhenomenon(p) {
    if (p === phenomenon) return;
    setPhenomenon(p);
    setPresetId(null);
    setArea(null);
    setPolygon(null);
    setResult(null);
    setTimeline(null);
    setCloudTest(null);
  }

  function pickPreset(p) {
    setPresetId(p.id);
    setArea(p.bbox);
    setPolygon(null);
    setResult(null);
    setTimeline(null);
    setCloudTest(null);
    setDrawing(null);
    setError(null);
  }

  function onDrawn({ bbox, polygon: shape }) {
    setDrawing(null);
    const max = config?.max_span_deg ?? 0.75;
    if (bbox[2] - bbox[0] < 0.01 || bbox[3] - bbox[1] < 0.01) return setError("That area is too small — drag out at least about 1 km on each side.");
    if (bbox[2] - bbox[0] > max || bbox[3] - bbox[1] > max) return setError(`That area is too large — keep each side under about ${Math.round(max * 111)} km.`);
    setError(null);
    setPresetId(null);
    setArea(bbox);
    setPolygon(shape);
    setResult(null);
    setTimeline(null);
    setCloudTest(null);
  }

  const request = (after, cloudFraction) =>
    api("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bbox: area, polygon, before: dates.before, after, phenomenon, cloud: cloudFraction }),
    });

  // Re-run the analysis with the "after" window moved back one year at a time.
  async function buildTimeline() {
    const windows = [];
    for (let k = 0; k < 8; k++) {
      const w = dates.after.map((d) => shiftYears(d, -k));
      if (w[0] <= dates.before[1]) break;
      windows.unshift(w);
    }
    if (windows.length < 2) return setError("The two dates are too close together for a year-by-year timeline.");
    const items = [];
    setError(null);
    try {
      for (let i = 0; i < windows.length; i++) {
        setTimeline({ items: [...items], index: Math.max(0, items.length - 1), loading: `${i + 1} of ${windows.length}` });
        const r = await request(windows[i], cloud); // finished years come straight from the cache
        items.push({ year: r.after.window[1].slice(0, 4), result: r });
        setResult(r);
      }
      setResult(items[items.length - 1].result);
      setTimeline({ items, index: items.length - 1, loading: null });
    } catch (e) {
      setError(e.message);
      // keep the years that did finish; "Rebuild timeline" picks up the rest
      setTimeline(items.length > 1 ? { items, index: items.length - 1, loading: null } : null);
    }
  }

  function scrub(index) {
    setTimeline({ ...timeline, index });
    setResult(timeline.items[index].result);
  }

  async function analyze(cloudFraction = cloud) {
    if (!area || !dates) return;
    setBusy(true);
    setError(null);
    try {
      const r = await request(dates.after, cloudFraction);
      setTimeline(null);
      setCloudTest(null);
      setResult(r);
      selectFused(r.best_fused);
      setOverlay(r.reference.available ? "errors" : "detected");
      setCollapsed(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  // Re-run at several synthetic-cloud levels and plot detection F1 for each input.
  async function runCloudTest() {
    const points = [];
    setError(null);
    try {
      for (let i = 0; i < CLOUD_LEVELS.length; i++) {
        setCloudTest({ points: [...points], loading: `${i + 1} of ${CLOUD_LEVELS.length}` });
        points.push({ cloud: CLOUD_LEVELS[i], result: await request(dates.after, CLOUD_LEVELS[i]) });
      }
      setCloudTest({ points, loading: null });
    } catch (e) {
      setError(e.message);
      setCloudTest(points.length > 1 ? { points, loading: null } : null);
    }
  }

  // One selection drives both the map image and the change overlay.
  function selectInput(key) {
    setVariant(key);
    setBase(key === "sar" ? "sar" : key === "optical" || key === "stack" ? "optical" : "fused");
    setOverlay((o) => (o === "off" ? "detected" : o));
  }

  function selectFused(key) {
    setFusedVariant(key);
    selectInput(key);
  }

  // The band stack is not a single image, so "Fused" imagery needs a pixel-level method.
  const baseLayer = base === "fused" ? (fusedVariant === "stack" ? "optical" : fusedVariant) : base;
  const info = PHENOMENA[phenomenon];
  const rows = result
    ? [
        { key: "sar", name: "Radar only", tone: "sar", v: result.variants.sar },
        { key: "optical", name: "Optical only", tone: "optical", v: result.variants.optical },
        { key: fusedVariant, name: "Fused", tone: "fused", v: result.variants[fusedVariant], fused: true },
      ]
    : [];
  const headline = result?.variants[variant];
  const datesInvalid = dates && (dates.before[0] >= dates.before[1] || dates.after[0] >= dates.after[1] || dates.before[1] >= dates.after[0]);

  return (
    <div className="app">
      <MapView
        area={area}
        polygon={polygon}
        opacity={opacity}
        result={result}
        baseLayer={baseLayer}
        overlays={{ overlay, variant, blind: true }}
        leftCollapsed={collapsed && !!result}
        drawing={drawing}
        onDrawn={onDrawn}
        split={split}
        onSplit={setSplit}
      />

      {/* ------------------------------------------------ control panel */}
      {collapsed && result ? (
        <aside className="panel left compact">
          <header className="brand">
            <div className="mark"><i className="sar" /><i className="optical" /><i className="fused" /></div>
            <div><h1>Overcast</h1></div>
          </header>
          <dl className="summary">
            <dt>Watching</dt><dd>{info.label}</dd>
            <dt>Where</dt><dd>{presets.find((p) => p.id === presetId)?.name ?? `Custom ${polygon ? "shape" : "area"} · ${km(area)}`}</dd>
            <dt>When</dt><dd>{dates.before[0].slice(0, 7)} → {dates.after[1].slice(0, 7)}</dd>
            {result.cloud.simulated_pct > 0 && <><dt>Cloud</dt><dd>{result.cloud.simulated_pct}% synthetic</dd></>}
          </dl>
          <button className="ghost" onClick={() => setCollapsed(false)}>Change area, dates or cloud</button>
          {error && <p className="warn">{error}</p>}
        </aside>
      ) : (
      <aside className="panel left">
        <header className="brand">
          <div className="mark"><i className="sar" /><i className="optical" /><i className="fused" /></div>
          <div>
            <h1>Overcast</h1>
            <p>Land-change monitoring that keeps working under cloud</p>
          </div>
        </header>

        <section>
          <h2><b>1</b> What to watch</h2>
          <div className="segmented">
            {Object.entries(PHENOMENA).map(([k, p]) => (
              <button key={k} className={k === phenomenon ? "on" : ""} onClick={() => pickPhenomenon(k)}>{p.label}</button>
            ))}
          </div>
        </section>

        <section>
          <h2><b>2</b> Where</h2>
          <div className="presets">
            {presets.map((p) => (
              <button key={p.id} className={`preset ${p.id === presetId ? "on" : ""}`} onClick={() => pickPreset(p)}>
                <strong>{p.name}</strong>
                <span>{p.place}</span>
                <em>{p.blurb}</em>
              </button>
            ))}
          </div>
          <div className="draw">
            <button className={`ghost ${drawing === "rect" ? "on" : ""}`} onClick={() => { setDrawing(drawing === "rect" ? null : "rect"); setError(null); }}>▭ Draw a box</button>
            <button className={`ghost ${drawing === "polygon" ? "on" : ""}`} onClick={() => { setDrawing(drawing === "polygon" ? null : "polygon"); setError(null); }}>⬠ Draw any shape</button>
          </div>
          {drawing === "rect" && <p className="hint">Click and drag on the map.</p>}
          {drawing === "polygon" && <p className="hint">Click to add corners. Double-click, or click the first corner, to finish.</p>}
          {area && !presetId && !drawing && <p className="hint">Custom {polygon ? "shape" : "area"} · {km(area)}</p>}
        </section>

        {dates && (
          <section>
            <h2><b>3</b> When</h2>
            {["before", "after"].map((k) => (
              <div className="daterow" key={k}>
                <label>{k === "before" ? "Before" : "After"}</label>
                <input type="date" value={dates[k][0]} max={dates[k][1]} onChange={(e) => setDates({ ...dates, [k]: [e.target.value, dates[k][1]] })} />
                <span>to</span>
                <input type="date" value={dates[k][1]} min={dates[k][0]} onChange={(e) => setDates({ ...dates, [k]: [dates[k][0], e.target.value] })} />
              </div>
            ))}
            <p className="hint">Each window is merged into one image. Two to three months works well.</p>
            {datesInvalid && <p className="warn">Each range must run forwards, and “before” must end before “after” starts.</p>}
          </section>
        )}

        <section>
          <h2><b>4</b> Cloud stress test <small>optional</small></h2>
          <div className="slider">
            <input type="range" min="0" max="90" step="10" value={cloud * 100} onChange={(e) => setCloud(e.target.value / 100)} />
            <output>{Math.round(cloud * 100)}%</output>
          </div>
          <p className="hint">Hide part of the “after” optical image behind synthetic cloud to see which inputs still detect change.</p>
        </section>

        <button className="primary" disabled={!area || busy || datesInvalid || !config?.models_ready} onClick={() => analyze()}>
          {busy ? "Analysing…" : result ? "Run again" : "Analyse this area"}
        </button>
        {!area && !error && <p className="hint center">Pick a place or draw an area to begin.</p>}
        {config && !config.models_ready && <p className="warn">The detection models are not trained yet.</p>}
        {error && <p className="warn">{error}</p>}
        {result && <button className="ghost" style={{ marginTop: 10 }} onClick={() => setCollapsed(true)}>Hide settings</button>}
      </aside>
      )}

      {/* ------------------------------------------------ map toolbar */}
      {result && (
        <div className="toolbar">
          <span className="tb-label">Image</span>
          <div className="segmented small">
            {BASE_LAYERS.map(([k, label]) => (
              <button key={k} className={base === k ? "on" : ""} onClick={() => setBase(k)}
                disabled={k === "fused" && fusedVariant === "stack"}
                title={k === "fused" ? (fusedVariant === "stack" ? "The band stack is not a single image; pick IHS, PCA or Wavelet to view a fused image" : `${result.variants[fusedVariant].label} image`) : undefined}>
                {k === "fused" && fusedVariant !== "stack" ? `Fused · ${FUSED_VARIANTS.find(([v]) => v === fusedVariant)[1]}` : label}
              </button>
            ))}
          </div>
          <span className="tb-label">Change</span>
          <div className="segmented small">
            <button className={overlay === "detected" ? "on" : ""} onClick={() => setOverlay("detected")}>Detected</button>
            {result.reference.available && <button className={overlay === "errors" ? "on" : ""} onClick={() => setOverlay("errors")}>vs reference</button>}
            <button className={overlay === "off" ? "on" : ""} onClick={() => setOverlay("off")}>Off</button>
          </div>
          {overlay !== "off" && <input className="opacity" type="range" min="0.2" max="1" step="0.05" value={opacity} onChange={(e) => setOpacity(+e.target.value)} title="Overlay opacity" aria-label="Overlay opacity" />}
          {overlay === "errors" && (
            <div className="legend inline"><i className="dot ok" /> Correct <i className="dot fa" /> False alarm <i className="dot miss" /> Missed</div>
          )}
        </div>
      )}

      {busy && (
        <div className="progress">
          <div className="spinner" />
          <div>
            <strong>{STEPS[step]}…</strong>
            <span>A new area takes about 30–60 seconds. Repeat runs are instant.</span>
          </div>
        </div>
      )}

      {/* ------------------------------------------------ results */}
      {result && headline && (
        <aside className="panel right">
          <section className="headline">
            <span className="eyebrow">{info.label} · {result.before.window[0].slice(0, 4)} → {result.after.window[1].slice(0, 4)} · {headline.label}</span>
            {result.reference.available ? (
              <>
                <div className="versus">
                  <div><span>Detected</span><b>{fmt(headline.area_ha)} <small>ha</small></b></div>
                  <div><span>Reference</span><b>{fmt(result.reference.area_ha)} <small>ha</small></b></div>
                </div>
                <p className="verdict">
                  Found <b>{Math.round(headline.scores.recall * 100)}%</b> of the {info.noun} the reference records.{" "}
                  <b>{Math.round(headline.scores.precision * 100)}%</b> of what it flagged is confirmed; the rest are false alarms.
                </p>
              </>
            ) : (
              <div className="big">{fmt(headline.area_ha)} <small>ha</small></div>
            )}
            <p>{result.reference.available ? "Detected area is" : info.unit + ":"} {headline.share_pct}% of the {fmt(result.grid.area_ha)} ha analysed, at {result.grid.pixel_m} m per pixel.</p>
          </section>

          <section>
            <h3>What each input found</h3>
            {result.cloud.after_gap_pct > 0.5 && (
              <p className="note">
                {result.cloud.simulated_pct > 0 ? `${result.cloud.simulated_pct}% synthetic cloud applied. ` : ""}
                Optical could not see {result.cloud.after_gap_pct}% of the “after” image.
              </p>
            )}
            <div className="rows">
              {rows.map((r) => (
                <button key={r.name} className={`row ${r.tone} ${variant === r.key ? "on" : ""}`} onClick={() => selectInput(r.key)}>
                  <div className="row-top">
                    <span className="swatch" />
                    <strong>{r.name}</strong>
                    <span className="area">{fmt(r.v.area_ha)} ha</span>
                  </div>
                  {r.v.scores ? (
                    <div className="scores">
                      {["precision", "recall", "f1"].map((m) => (
                        <div key={m} className={m}>
                          <label>{m === "f1" ? "F1" : m}</label>
                          <div className="bar"><i style={{ width: `${r.v.scores[m] * 100}%` }} /></div>
                          <span>{r.v.scores[m].toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="scores-none">Unseen-region F1: {r.v.holdout.clear.f1.toFixed(2)} clear · {r.v.holdout.cloudy.f1.toFixed(2)} cloudy</div>
                  )}
                  {r.v.blind_pct > 0.5 && <div className="blind">Blind over {r.v.blind_pct}% of the area</div>}
                </button>
              ))}
            </div>
            <div className="chips">
              <span>Fusion method</span>
              {FUSED_VARIANTS.map(([k, label]) => (
                <button key={k} className={fusedVariant === k ? "on" : ""} onClick={() => selectFused(k)}>
                  {label}{k === result.best_fused ? " ★" : ""}
                </button>
              ))}
            </div>
            <p className="hint">
              {result.reference.available
                ? `Scored against ${result.reference.source} (${result.reference.years.join(" → ")}), which shows ${fmt(result.reference.area_ha)} ha of ${info.noun}. The same detector runs on every input; only the input changes.`
                : "No reference data covers these dates (forest loss: 2001–2024; urban growth: 2017–2023), so scores shown are from regions the models never trained on."}
            </p>
          </section>

          <section>
            <h3>Cloud stress test</h3>
            {cloudTest && cloudTest.points.length > 1 && (
              <CloudChart points={cloudTest.points} fused={fusedVariant} fusedLabel={result.variants[fusedVariant].label} />
            )}
            {!cloudTest && (
              <p className="hint">
                {result.reference.available
                  ? "Hide 0–60% of the optical image behind synthetic cloud and see how each input's accuracy holds up."
                  : "Needs reference data for these dates to score each input."}
              </p>
            )}
            {cloudTest?.loading && <p className="hint">Running cloud level {cloudTest.loading}…</p>}
            {result.reference.available && !cloudTest?.loading && (
              <button className="ghost" onClick={runCloudTest} disabled={busy || !!timeline?.loading}>{cloudTest ? "Run again" : "Run cloud test (0–60%)"}</button>
            )}
          </section>

          <section>
            <h3>Year by year</h3>
            {timeline && timeline.items.length > 0 ? (
              <Timeline timeline={timeline} variant={fusedVariant} onScrub={scrub} />
            ) : (
              !timeline && <p className="hint">Re-run the analysis for each year between your two dates and scrub through the change as it builds up.</p>
            )}
            {timeline?.loading && <p className="hint">Analysing year {timeline.loading}…</p>}
            {!timeline?.loading && (
              <button className="ghost" onClick={buildTimeline} disabled={busy}>{timeline ? "Rebuild timeline" : "Build timeline"}</button>
            )}
          </section>

          <section>
            <h3>Cloud calendar · {calendar?.year ?? "…"}</h3>
            {calendar ? <Calendar data={calendar} /> : <p className="hint">Counting acquisitions…</p>}
          </section>

          <section>
            <h3>Fusion image quality</h3>
            <table>
              <thead><tr><th /><th title="Spectral angle, degrees. Lower is closer to the optical colours.">SAM°</th><th title="Relative spectral error. Lower is better.">ERGAS</th><th title="Structural similarity to the optical image.">SSIM opt</th><th title="Structural similarity to the radar image.">SSIM SAR</th><th title="Information content, bits.">Entropy</th></tr></thead>
              <tbody>
                {FUSION_VIEWS.map(([k, label]) => {
                  const q = result.quality[k] || {};
                  return <tr key={k}><td>{label}</td><td>{q.sam_deg ?? "–"}</td><td>{q.ergas ?? "–"}</td><td>{q.ssim_optical ?? "–"}</td><td>{q.ssim_sar ?? "–"}</td><td>{q.entropy ?? "–"}</td></tr>;
                })}
              </tbody>
            </table>
            <p className="hint">Reported for context. Detection accuracy above is what decides whether fusion helped.</p>
          </section>

          <section>
            <h3>Export</h3>
            <a className="ghost link" href={`/api/runs/${result.id}/report.html?variant=${variant}`} target="_blank" rel="noreferrer">Open printable report</a>
            <a className="ghost link" href={`/api/runs/${result.id}/change.geojson?variant=${variant}`} download>Download change polygons (GeoJSON)</a>
            <p className="hint">
              Optical: {result.after.optical.dates_used.length} of {result.after.optical.scenes_found} scenes used · Radar: {result.after.sar.dates_used.length} of {result.after.sar.scenes_found} scenes used
            </p>
          </section>
        </aside>
      )}
    </div>
  );
}

function Timeline({ timeline, variant, onScrub }) {
  const { items, index, loading } = timeline;
  const max = Math.max(1, ...items.map((it) => it.result.variants[variant].area_ha));
  return (
    <div className="timeline">
      <div className="tl-bars">
        {items.map((it, i) => (
          <button key={it.year} className={i === index ? "on" : ""} onClick={() => !loading && onScrub(i)} title={`${fmt(it.result.variants[variant].area_ha)} ha by ${it.year}`}>
            <i style={{ height: `${(it.result.variants[variant].area_ha / max) * 100}%` }} />
            <span>{it.year}</span>
          </button>
        ))}
      </div>
      {!loading && (
        <input type="range" min="0" max={items.length - 1} step="1" value={index} onChange={(e) => onScrub(+e.target.value)} aria-label="Timeline year" />
      )}
      <p className="hint">Change detected between {items[index].result.before.window[1].slice(0, 4)} and {items[index].year}: {fmt(items[index].result.variants[variant].area_ha)} ha.</p>
    </div>
  );
}

function Calendar({ data }) {
  const max = Math.max(1, ...data.months.map((m) => Math.max(m.optical_total, m.sar)));
  const clear = data.months.reduce((a, m) => a + m.optical_clear, 0);
  const sar = data.months.reduce((a, m) => a + m.sar, 0);
  const dark = data.months.filter((m) => m.optical_clear === 0).length;
  return (
    <div className="calendar">
      <div className="cal-grid">
        {data.months.map((m) => (
          <div key={m.month} className="cal-col" title={`${m.optical_clear} clear optical, ${m.optical_partial} partly cloudy, ${m.sar} radar`}>
            <div className="cal-bars">
              <i className="optical" style={{ height: `${(m.optical_clear / max) * 100}%` }} />
              <i className="sar" style={{ height: `${(m.sar / max) * 100}%` }} />
            </div>
            <span>{MONTHS[m.month - 1]}</span>
          </div>
        ))}
      </div>
      <div className="legend"><i className="dot optical" /> Clear optical days <i className="dot sar" /> Radar days</div>
      <p className="hint">{clear} clear optical days against {sar} radar days this year{dark > 0 ? `; ${dark} month${dark > 1 ? "s" : ""} had no clear optical image at all` : ""}.</p>
    </div>
  );
}

function CloudChart({ points, fused, fusedLabel }) {
  const W = 330, H = 150, L = 30, B = 22, T = 8, R = 8;
  const series = [["sar", "Radar only", "var(--sar)"], ["optical", "Optical only", "var(--optical)"], [fused, fusedLabel, "var(--fused)"]];
  const f1 = (p, k) => p.result.variants[k].scores?.f1 ?? 0;
  const top = Math.max(0.5, Math.ceil(Math.max(...points.flatMap((p) => series.map(([k]) => f1(p, k)))) * 10) / 10);
  const x = (c) => L + (c / 0.6) * (W - L - R);
  const y = (v) => T + (1 - v / top) * (H - T - B);
  const last = points[points.length - 1];
  return (
    <div className="cloudchart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Detection F1 against synthetic cloud cover for each input">
        {[0, top / 2, top].map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="grid" />
            <text x={L - 6} y={y(v) + 3} textAnchor="end">{v.toFixed(1)}</text>
          </g>
        ))}
        {CLOUD_LEVELS.map((c) => <text key={c} x={x(c)} y={H - 6} textAnchor="middle">{Math.round(c * 100)}%</text>)}
        {series.map(([k, , color]) => (
          <g key={k} style={{ color }}>
            <polyline fill="none" stroke="currentColor" strokeWidth="2" points={points.map((p) => `${x(p.cloud)},${y(f1(p, k))}`).join(" ")} />
            {points.map((p) => <circle key={p.cloud} cx={x(p.cloud)} cy={y(f1(p, k))} r="3" fill="currentColor"><title>{`${Math.round(p.cloud * 100)}% cloud: F1 ${f1(p, k).toFixed(2)}`}</title></circle>)}
          </g>
        ))}
      </svg>
      <div className="legend">
        {series.map(([k, label, color]) => <span key={k}><i className="dot" style={{ background: color }} /> {label}</span>)}
      </div>
      <p className="hint">
        Detection F1 as synthetic cloud hides more of the optical image. At {Math.round(last.cloud * 100)}% cloud:{" "}
        {series.map(([k, label]) => `${label} ${f1(last, k).toFixed(2)}`).join(" · ")}.
      </p>
    </div>
  );
}
