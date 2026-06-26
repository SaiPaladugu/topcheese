import { ImageResponse } from "next/og";
import A from "../data/analysis.json";

export const alt = "Topcheese044 — Certified Chud scouting report";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  const S = A.summary;
  const acc = A.ml ? A.ml.cvAccuracy : 80;
  const stat = (label, value, color) => ({
    label, value, color,
  });
  const stats = [
    stat("WIN RATE", `${S.wr}%`, "#f85149"),
    stat("RANK", "Diamond III", "#58a6ff"),
    stat("AI-PREDICTABLE", `${acc}%`, "#d29922"),
    stat("CARRIED BY", "Tony", "#3fb950"),
  ];
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column",
          background: "linear-gradient(135deg, #1c2330, #0f1419)", color: "#e6edf3",
          padding: "64px 72px", fontFamily: "sans-serif", justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 30, color: "#8b949e", display: "flex" }}>
            Topcheese044 #NA1 · solo queue scouting report
          </div>
          <div style={{ fontSize: 92, fontWeight: 800, marginTop: 8, display: "flex" }}>
            CERTIFIED CHUD 🤡
          </div>
          <div style={{ fontSize: 34, color: "#8b949e", marginTop: 10, display: "flex" }}>
            A 50.5% player chauffeured to Diamond by a friend with 5 accounts.
          </div>
        </div>
        <div style={{ display: "flex", gap: 28 }}>
          {stats.map((s) => (
            <div
              key={s.label}
              style={{
                display: "flex", flexDirection: "column", padding: "20px 28px",
                background: "#161b22", border: "1px solid #30363d", borderRadius: 16,
              }}
            >
              <div style={{ fontSize: 22, color: "#8b949e", display: "flex" }}>{s.label}</div>
              <div style={{ fontSize: 48, fontWeight: 800, color: s.color, display: "flex" }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 26, color: "#58a6ff", display: "flex" }}>
          topcheese044.vercel.app — 17 sections of data-backed disrespect
        </div>
      </div>
    ),
    { ...size }
  );
}
