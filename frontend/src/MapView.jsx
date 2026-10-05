import { useEffect, useRef, useState } from "react";
import L from "leaflet";

const BASEMAP = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const LABELS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}";
const ATTRIB =
  'Basemap: Esri, HERE, Garmin, &copy; OpenStreetMap · Sentinel-1/2: Copernicus, via Microsoft Planetary Computer';

/**
 * Leaflet map with a before/after swipe, a change overlay and rectangle drawing.
 * Leaflet owns the DOM here; React only pushes props in through effects.
 */
export default function MapView({ area, polygon, result, baseLayer, overlays, opacity, drawing, onDrawn, split, onSplit }) {
  const el = useRef(null);
  const map = useRef(null);
  const layers = useRef({});
  const areaRect = useRef(null);
  const splitRef = useRef(split);
  const [dragging, setDragging] = useState(false);

  // ---- map setup
  useEffect(() => {
    const m = L.map(el.current, { zoomControl: false, attributionControl: true }).setView([20.6, 79], 5);
    L.control.zoom({ position: "bottomright" }).addTo(m);
    L.tileLayer(BASEMAP, { attribution: ATTRIB, maxNativeZoom: 16, maxZoom: 18 }).addTo(m);
    L.tileLayer(LABELS, { maxNativeZoom: 16, maxZoom: 18 }).addTo(m);
    for (const [name, z] of [["before", 410], ["after", 411], ["blind", 420], ["reference", 421], ["change", 422]]) {
      m.createPane(name).style.zIndex = z;
      m.getPane(name).style.pointerEvents = "none";
    }
    m.on("move zoom resize", () => clip(m, splitRef.current));
    map.current = m;
    return () => m.remove();
  }, []);

  function clip(m, ratio) {
    const size = m.getSize();
    const nw = m.containerPointToLayerPoint([0, 0]);
    const se = m.containerPointToLayerPoint(size);
    const x = nw.x + size.x * ratio;
    m.getPane("before").style.clip = `rect(${nw.y}px, ${x}px, ${se.y}px, ${nw.x}px)`;
    m.getPane("after").style.clip = `rect(${nw.y}px, ${se.x}px, ${se.y}px, ${x}px)`;
  }

  useEffect(() => {
    splitRef.current = split;
    if (map.current) clip(map.current, split);
  }, [split]);

  // ---- selected area outline
  useEffect(() => {
    const m = map.current;
    if (areaRect.current) areaRect.current.remove();
    areaRect.current = null;
    if (!area) return;
    const [w, s, e, n] = area;
    const bounds = [[s, w], [n, e]];
    const style = { color: "#f4f0e8", weight: 1.5, dashArray: result ? null : "6 6", fill: !result, fillOpacity: 0.06, interactive: false };
    areaRect.current = (polygon ? L.polygon(polygon.map(([lon, lat]) => [lat, lon]), style) : L.rectangle(bounds, style)).addTo(m);
    m.flyToBounds(bounds, { padding: [60, 60], paddingTopLeft: [400, 90], paddingBottomRight: [result ? 420 : 60, 60], duration: 0.8 });
  }, [area, polygon, !!result]);

  // ---- imagery + overlays
  useEffect(() => {
    const m = map.current;
    Object.values(layers.current).forEach((l) => l.remove());
    layers.current = {};
    if (!result) return;
    const add = (key, url, pane, opacity = 1) => {
      if (!url) return;
      layers.current[key] = L.imageOverlay(url, result.bounds, { pane, opacity, className: "crisp" }).addTo(m);
    };
    add("before", result.layers.before[baseLayer], "before");
    add("after", result.layers.after[baseLayer], "after");
    if (overlays.blind) add("blind", result.layers.change.optical_blind, "blind");
    if (overlays.reference) add("reference", result.layers.change.reference, "reference", 0.85);
    if (overlays.change) add("change", result.layers.change[overlays.variant], "change", opacity);
    clip(m, splitRef.current);
  }, [result, baseLayer, overlays.change, overlays.reference, overlays.blind, overlays.variant]);

  useEffect(() => {
    layers.current.change?.setOpacity(opacity);
  }, [opacity]);

  // ---- drawing: drag a rectangle, or click out any shape
  useEffect(() => {
    const m = map.current;
    if (!drawing) return;
    const style = { color: "#ff8a3d", weight: 2, fillOpacity: 0.12 };
    const round = (v) => +v.toFixed(5);
    m.getContainer().style.cursor = "crosshair";
    let cleanup = () => {};

    if (drawing === "rect") {
      m.dragging.disable();
      let start = null;
      let rect = null;
      const down = (e) => {
        start = e.latlng;
        rect = L.rectangle([start, start], style).addTo(m);
      };
      const move = (e) => rect && rect.setBounds([start, e.latlng]);
      const up = (e) => {
        if (!rect) return;
        const b = L.latLngBounds(start, e.latlng);
        rect.remove();
        rect = null;
        onDrawn({ bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map(round), polygon: null });
      };
      m.on("mousedown", down).on("mousemove", move).on("mouseup", up);
      cleanup = () => {
        m.off("mousedown", down).off("mousemove", move).off("mouseup", up);
        m.dragging.enable();
        if (rect) rect.remove();
      };
    } else {
      m.doubleClickZoom.disable();
      const pts = [];
      const shape = L.polygon([], style).addTo(m);
      const dots = L.layerGroup().addTo(m);
      const finish = () => {
        if (pts.length < 3) return;
        const b = L.latLngBounds(pts);
        onDrawn({
          bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map(round),
          polygon: pts.map((p) => [round(p.lng), round(p.lat)]),
        });
      };
      const click = (e) => {
        // clicking back on the first corner closes the shape
        if (pts.length >= 3 && m.latLngToContainerPoint(pts[0]).distanceTo(e.containerPoint) < 12) return finish();
        pts.push(e.latlng);
        L.circleMarker(e.latlng, { radius: 4, color: "#ff8a3d", fillColor: "#14181f", fillOpacity: 1, weight: 2 }).addTo(dots);
        shape.setLatLngs(pts);
      };
      const move = (e) => pts.length && shape.setLatLngs([...pts, e.latlng]);
      const dbl = () => {
        pts.pop(); // the double-click's second click added a duplicate corner
        finish();
      };
      m.on("click", click).on("mousemove", move).on("dblclick", dbl);
      cleanup = () => {
        m.off("click", click).off("mousemove", move).off("dblclick", dbl);
        shape.remove();
        dots.remove();
        setTimeout(() => m.doubleClickZoom.enable(), 0);
      };
    }
    return () => {
      cleanup();
      m.getContainer().style.cursor = "";
    };
  }, [drawing]);

  // ---- swipe handle
  useEffect(() => {
    if (!dragging) return;
    const move = (e) => {
      const box = el.current.getBoundingClientRect();
      onSplit(Math.min(0.98, Math.max(0.02, (e.clientX - box.left) / box.width)));
    };
    const stop = () => setDragging(false);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
    };
  }, [dragging]);

  return (
    <div className="map-wrap">
      <div ref={el} className="map" />
      {result && (
        <div className="swipe" style={{ left: `${split * 100}%` }} onPointerDown={(e) => { e.preventDefault(); setDragging(true); }}>
          <span className="swipe-tag left">Before</span>
          <span className="swipe-tag right">After</span>
          <div className="swipe-grip" aria-label="Drag to compare before and after">◂ ▸</div>
        </div>
      )}
    </div>
  );
}
