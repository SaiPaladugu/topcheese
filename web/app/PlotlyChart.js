"use client";
import { useEffect, useRef } from "react";

// Minimal, robust Plotly wrapper — loads plotly.js-dist-min on the client only.
export default function PlotlyChart({ data, layout, style }) {
  const ref = useRef(null);
  useEffect(() => {
    let alive = true;
    let Plotly = null;
    import("plotly.js-dist-min").then((mod) => {
      Plotly = mod.default || mod;
      if (alive && ref.current) {
        Plotly.newPlot(ref.current, data, layout, {
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ["toImage", "sendDataToCloud"],
          displaylogo: false,
        });
      }
    });
    return () => {
      alive = false;
      if (Plotly && ref.current) Plotly.purge(ref.current);
    };
  }, [data, layout]);
  return <div ref={ref} style={style} />;
}
