"use client";
import dynamic from "next/dynamic";

function Loading({ what }) {
  return (
    <div style={{
      height: 520, display: "flex", alignItems: "center", justifyContent: "center",
      color: "#8b949e", background: "#11161d", border: "1px solid #30363d", borderRadius: 12,
    }}>
      rendering {what}… (drag to orbit once it loads)
    </div>
  );
}

const Scatter3D = dynamic(() => import("./Viz3D").then((m) => m.Scatter3D), {
  ssr: false, loading: () => <Loading what="3D game cloud" />,
});
const Surface3D = dynamic(() => import("./Viz3D").then((m) => m.Surface3D), {
  ssr: false, loading: () => <Loading what="win-rate surface" />,
});
const Terrain3D = dynamic(() => import("./Terrain3D"), {
  ssr: false, loading: () => <Loading what="valley of death" />,
});

export default function Interactive3D() {
  return (
    <section id="threed">
      <h2>The 4th dimension — interactive &amp; 3D 🧊</h2>
      <p className="lead">
        Static charts are for cowards (him). These you can actually <b>grab, spin, and zoom</b>.
        Drag any of them. Hover for details. Marvel at how much engineering went into proving a
        Diamond ADC is mid.
      </p>

      <h3 style={{ margin: "20px 0 4px 2px", fontSize: 17 }}>
        Every game, floating in the void of his mediocrity
      </h3>
      <p className="lead" style={{ marginTop: 0 }}>
        All 795 ranked games plotted in 3D — <b>gold@14 × kill participation × deaths</b>, green
        wins, red losses. Spin it and watch the red cloud sink into the &quot;lots of deaths, no
        gold, no KP&quot; corner like sediment.
      </p>
      <div className="chart"><Scatter3D /></div>

      <h3 style={{ margin: "24px 0 4px 2px", fontSize: 17 }}>
        The win-rate landscape (a surface he refuses to climb)
      </h3>
      <p className="lead" style={{ marginTop: 0 }}>
        His win rate as an actual 3D terrain over <b>gold@14 × kill participation</b>. The summit
        (get a lead, join fights) is right there. He spends his career camped in the swampy red
        lowlands, farming.
      </p>
      <div className="chart"><Surface3D /></div>

      <h3 style={{ margin: "24px 0 4px 2px", fontSize: 17 }}>
        The Valley of Death (a fully 3D render of where he dies)
      </h3>
      <p className="lead" style={{ marginTop: 0 }}>
        A real-time 3D heightfield of his {`4,552`} deaths, side-normalized. The mountains are
        where he dies most. Orbit the terrain. Those aren&apos;t the Alps — that&apos;s his bot lane
        and his own jungle. The only peak missing is the StairMaster.
      </p>
      <div className="chart" style={{ padding: 0, overflow: "hidden" }}><Terrain3D /></div>
      <div className="callout loss">
        <h3>WebGL was invented for this</h3>
        <p>
          Somewhere, a graphics engineer spent a decade so the world could render cinematic 3D
          worlds. We used it to build an orbit-able mountain range out of one chud&apos;s deaths.
          Worth it. Now go for a jog and stop dying on the raptor camp.
        </p>
      </div>
    </section>
  );
}
