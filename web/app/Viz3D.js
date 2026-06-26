"use client";
import PlotlyChart from "./PlotlyChart";
import games from "../data/games.json";
import surface from "../data/surface.json";

const BG = "#0f1419", FG = "#e6edf3", GRID = "#30363d", WIN = "#3fb950", LOSS = "#f85149";

const axis = (title) => ({
  title: { text: title, font: { color: FG } },
  color: FG, gridcolor: GRID, zerolinecolor: GRID,
  backgroundcolor: "#11161d", showbackground: true,
});

// 3D scatter — every ranked game floating in (gold@14, KP, deaths) space.
export function Scatter3D() {
  const mk = (gs, name, color) => ({
    type: "scatter3d", mode: "markers", name,
    x: gs.map((g) => g.g14), y: gs.map((g) => g.kp), z: gs.map((g) => g.d),
    text: gs.map((g) => `${g.champ} — ${g.win ? "WIN" : "LOSS"}<br>gold@14 ${g.g14} · KP ${g.kp}% · ${g.d} deaths`),
    hoverinfo: "text",
    marker: { size: 3, color, opacity: 0.72 },
  });
  const data = [
    mk(games.filter((g) => g.win), "WIN", WIN),
    mk(games.filter((g) => !g.win), "LOSS", LOSS),
  ];
  const layout = {
    paper_bgcolor: BG, font: { color: FG }, height: 560,
    margin: { l: 0, r: 0, t: 6, b: 0 }, legend: { x: 0, y: 0.95 },
    scene: {
      xaxis: axis("gold diff @14"), yaxis: axis("kill participation %"), zaxis: axis("deaths"),
      camera: { eye: { x: 1.7, y: 1.5, z: 0.85 } },
    },
  };
  return <PlotlyChart data={data} layout={layout} style={{ width: "100%" }} />;
}

// 3D surface — win% as a literal landscape over gold@14 × kill participation.
export function Surface3D() {
  const data = [{
    type: "surface", x: surface.x, y: surface.y, z: surface.z, connectgaps: true,
    colorscale: [[0, LOSS], [0.5, "#caa23a"], [1, WIN]], cmin: 20, cmax: 80,
    colorbar: { title: { text: "win %", font: { color: FG } }, tickfont: { color: FG } },
    contours: { z: { show: true, usecolormap: true, project: { z: true } } },
  }];
  const layout = {
    paper_bgcolor: BG, font: { color: FG }, height: 560,
    margin: { l: 0, r: 0, t: 6, b: 0 },
    scene: {
      xaxis: axis("gold diff @14"), yaxis: axis("kill participation %"), zaxis: axis("win %"),
      camera: { eye: { x: 1.8, y: 1.6, z: 0.8 } },
    },
  };
  return <PlotlyChart data={data} layout={layout} style={{ width: "100%" }} />;
}
