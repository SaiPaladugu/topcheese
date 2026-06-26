import A from "../data/analysis.json";

const S = A.summary;
const B = A.benchmark;

function wrClass(wr, ref = 51.5) {
  if (wr >= ref + 1.5) return "good";
  if (wr < 48) return "bad";
  return "mid";
}

function Chart({ src, cap }) {
  return (
    <figure className="chart">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={cap} />
      <figcaption className="cap">{cap}</figcaption>
    </figure>
  );
}

// champion verdicts
function verdict(c) {
  if (c.games < 10) return { t: "small sample", k: "mid" };
  if (c.wr >= 54) return { t: "spam ✅", k: "good" };
  if (c.wr < 46) return { t: "bench ❌", k: "bad" };
  return { t: "situational", k: "mid" };
}

const BENCH_LABELS = {
  csPerMin: "CS / min",
  kp: "Kill participation %",
  teamDmgPct: "Team damage %",
  dmgPerMin: "Damage / min",
  goldPerMin: "Gold / min",
  deaths: "Deaths / game",
  visionPerMin: "Vision / min",
  controlWards: "Control wards",
  soloKills: "Solo kills",
  kda: "KDA",
  laneMinions10: "Lane CS @10",
};
const LOWER_BETTER = new Set(["deaths"]);

export default function Page() {
  const champs = A.champions.filter((c) => c.games >= 5);
  const worstEnemies = A.matchups.byEnemyAdc.slice(0, 8);
  const caitPairs = A.matchups.byPair.filter((p) => p.champion === "Caitlyn");
  const caitGood = [...caitPairs].sort((a, b) => b.wr - a.wr).slice(0, 6);
  const caitBad = [...caitPairs].sort((a, b) => a.wr - b.wr).slice(0, 6);
  const wlTop = A.winLoss.filter((r) => r.key !== "kda" && r.key !== "durationMin").slice(0, 8);

  return (
    <>
      <header className="hero">
        <div className="hero-inner">
          <h1>Topcheese044 — Solo Queue Coaching Report</h1>
          <p className="sub">
            {S.nGames} ranked games · {S.dateFrom} → {S.dateTo} · {S.rank} · ADC
          </p>
          <div className="badges">
            <span className="badge">
              Win rate <b>{S.wr}%</b> ({S.wins}–{S.losses})
            </span>
            <span className="badge">
              Games <b>{S.nGames}</b>
            </span>
            <span className="badge">
              Champions <b>{S.championsPlayed}</b>
            </span>
            <span className="badge">
              Diamond benchmark <b>{B.n} games</b>
            </span>
          </div>
        </div>
      </header>

      <div className="wrap">
        <nav className="toc">
          <a href="#diagnosis">Diagnosis</a>
          <a href="#decide">What decides games</a>
          <a href="#champs">Champions</a>
          <a href="#matchups">Matchups</a>
          <a href="#tilt">Tilt &amp; scheduling</a>
          <a href="#form">Form</a>
          <a href="#plan">Action plan</a>
        </nav>

        {/* ---------- DIAGNOSIS ---------- */}
        <section id="diagnosis">
          <h2>The diagnosis: a safe, clean farmer who under-converts</h2>
          <p className="lead">
            Benchmarked against {B.n} real Diamond ADCs, he is average on almost
            everything, with one consistent shape: he plays safe and farms his lane,
            but generates less damage, gold, and objective pressure than his peers.
          </p>
          <div className="cards">
            <div className="card">
              <div className="k">Deaths / game</div>
              <div className="v good">{B.hisMeans.deaths}</div>
              <div className="k">Diamond {B.means.deaths} · dies less ✅</div>
            </div>
            <div className="card">
              <div className="k">Kill participation</div>
              <div className="v bad">{B.hisMeans.kp}%</div>
              <div className="k">Diamond {B.means.kp}% · low 🚩</div>
            </div>
            <div className="card">
              <div className="k">Team damage share</div>
              <div className="v bad">{B.hisMeans.teamDmgPct}%</div>
              <div className="k">Diamond {B.means.teamDmgPct}% 🚩</div>
            </div>
            <div className="card">
              <div className="k">Control wards / game</div>
              <div className="v bad">{B.hisMeans.controlWards}</div>
              <div className="k">Diamond {B.means.controlWards} 🚩</div>
            </div>
          </div>
          <Chart src="/charts/benchmark.png" cap="Him vs Diamond-ADC baseline (100 = at rank average). Red = below peers." />
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th className="num">Him</th>
                  <th className="num">Diamond ADC</th>
                  <th className="num">vs peers</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(BENCH_LABELS).map((k) => {
                  const him = B.hisMeans[k];
                  const dia = B.means[k];
                  const lower = LOWER_BETTER.has(k);
                  const better = lower ? him <= dia : him >= dia;
                  return (
                    <tr key={k}>
                      <td>{BENCH_LABELS[k]}</td>
                      <td className="num">{him}</td>
                      <td className="num">{dia}</td>
                      <td className="num">
                        <span className={"pill " + (better ? "good" : "bad")}>
                          {better ? "✓" : "✗"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="callout">
            <h3>Read</h3>
            <p>
              He is not losing because of mechanics or farming — he wins lane on CS and
              avoids dying. He is losing because lane leads aren&apos;t turned into team
              impact. That&apos;s a decision-making problem, which climbs faster than a
              mechanics one.
            </p>
          </div>
        </section>

        {/* ---------- WHAT DECIDES GAMES ---------- */}
        <section id="decide">
          <h2>What actually decides his games</h2>
          <p className="lead">
            Every metric compared between his wins and losses, ranked by effect size
            (Cohen&apos;s d). Ignoring KDA (a scoreboard echo), the controllable
            differentiators are objective presence and gold conversion — bigger than
            laning itself.
          </p>
          <Chart src="/charts/winloss_effect.png" cap="What separates his wins from losses (standardized effect size)." />
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Differentiator</th>
                  <th className="num">In wins</th>
                  <th className="num">In losses</th>
                  <th className="num">Effect (d)</th>
                </tr>
              </thead>
              <tbody>
                {wlTop.map((r) => (
                  <tr key={r.key}>
                    <td>{r.label}</td>
                    <td className="num">{r.winMean}</td>
                    <td className="num">{r.lossMean}</td>
                    <td className="num">{r.cohensD}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Chart src="/charts/lane14_winloss.png" cap="Lane lead at 14 minutes: wins vs losses." />
          <div className="callout win">
            <h3>Headline</h3>
            <p>
              For this player, objective presence (dragon takedowns: {wlDragon()}) and
              gold generation outrank laning. He already wins lane — the leak is grouping
              for dragons and converting leads into gold, plates, and kills.
            </p>
          </div>
        </section>

        {/* ---------- CHAMPIONS ---------- */}
        <section id="champs">
          <h2>Champion pool</h2>
          <p className="lead">
            Caitlyn-dominant ({champPct("Caitlyn")}% of games). His best high-volume champ
            is actually Miss Fortune. Sivir is a heavy anchor he should bench.
          </p>
          <Chart src="/charts/champion_wr.png" cap="Win rate by champion (≥10 games). Reference line = his 51.5% average." />
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Champion</th>
                  <th className="num">Games</th>
                  <th className="num">WR</th>
                  <th className="num">Gold@14</th>
                  <th className="num">Dmg%</th>
                  <th className="num">KDA</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {champs.map((c) => {
                  const v = verdict(c);
                  return (
                    <tr key={c.champion}>
                      <td>{c.champion}</td>
                      <td className="num">{c.games}</td>
                      <td className="num">
                        <span className={"pill " + wrClass(c.wr)}>{c.wr}%</span>
                      </td>
                      <td className="num">{c.goldDiff14}</td>
                      <td className="num">{c.teamDmgPct}</td>
                      <td className="num">{c.kda}</td>
                      <td>
                        <span className={"pill " + v.k}>{v.t}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="callout loss">
            <h3>The Sivir problem</h3>
            <p>
              {sivir().games} games at {sivir().wr}% — his best CS/min yet his worst win
              rate, the classic sign of a champ he farms on but can&apos;t carry with.
              Replacing those games with his ~53% champs is worth roughly +9 wins.
            </p>
          </div>
        </section>

        {/* ---------- MATCHUPS ---------- */}
        <section id="matchups">
          <h2>Matchups — pick Caitlyn on purpose, not autopilot</h2>
          <p className="lead">
            Caitlyn&apos;s win rate swings wildly by enemy ADC. Into her bad matchups,
            lock Miss Fortune instead.
          </p>
          <div className="grid2">
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>✅ Caitlyn dominates</th>
                    <th className="num">G</th>
                    <th className="num">WR</th>
                  </tr>
                </thead>
                <tbody>
                  {caitGood.map((p) => (
                    <tr key={p.enemyAdc}>
                      <td>vs {p.enemyAdc}</td>
                      <td className="num">{p.games}</td>
                      <td className="num">
                        <span className="pill good">{p.wr}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>❌ Caitlyn struggles</th>
                    <th className="num">G</th>
                    <th className="num">WR</th>
                  </tr>
                </thead>
                <tbody>
                  {caitBad.map((p) => (
                    <tr key={p.enemyAdc}>
                      <td>vs {p.enemyAdc}</td>
                      <td className="num">{p.games}</td>
                      <td className="num">
                        <span className="pill bad">{p.wr}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <h3 style={{ margin: "24px 0 4px 2px", fontSize: 17 }}>
            Enemy ADCs that beat him regardless of pick
          </h3>
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Enemy ADC</th>
                  <th className="num">Games</th>
                  <th className="num">His WR</th>
                </tr>
              </thead>
              <tbody>
                {worstEnemies.map((m) => (
                  <tr key={m.enemyAdc}>
                    <td>vs {m.enemyAdc}</td>
                    <td className="num">{m.games}</td>
                    <td className="num">
                      <span className={"pill " + wrClass(m.wr)}>{m.wr}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ---------- TILT ---------- */}
        <section id="tilt">
          <h2>Tilt &amp; scheduling — when to queue, when to stop</h2>
          <p className="lead">
            When he plays matters as much as how. Local time inferred from his activity
            pattern as UTC{A.time.inferredUtcOffset} (US Central).
          </p>
          <div className="grid2">
            <div className="callout loss">
              <h3>🛑 Stop after 3 losses</h3>
              <p>
                His win rate drops to {streak("after 3+ losses")}% after three straight
                losses — by far his worst state. Continuing is a statistically losing bet.
              </p>
            </div>
            <div className="callout loss">
              <h3>🌙 No ranked after midnight</h3>
              <p>
                Midnight–1&nbsp;AM runs {hour(0)}–{hour(1)}% over {hourGames(0) + hourGames(1)}{" "}
                games. His evening window (8–9&nbsp;PM) is his best at {hour(20)}–{hour(21)}%.
              </p>
            </div>
          </div>
          <Chart src="/charts/streak_wr.png" cap="Win rate by streak state — losing streaks compound." />
          <Chart src="/charts/hour_wr.png" cap="Win rate by hour of day (local). Evening peaks, post-midnight collapses." />
          <Chart src="/charts/gamesperday_wr.png" cap="Win rate by games played that day (note: short days are confounded by quitting after losses)." />
        </section>

        {/* ---------- FORM ---------- */}
        <section id="form">
          <h2>Two-year form: a plateau</h2>
          <p className="lead">
            Rolling 50-game win rate has oscillated around 50% for two years — exactly
            what an average-everything profile produces. Breaking the plateau means
            raising the flagged metrics above.
          </p>
          <Chart src="/charts/form.png" cap="Rolling 50-game win rate over time." />
        </section>

        {/* ---------- PLAN ---------- */}
        <section id="plan">
          <h2>The action plan</h2>
          <ol className="plan">
            <li>
              <b>Bench Sivir.</b> Default to Caitlyn / Miss Fortune. Worth ~+9 wins on
              this sample size alone.
            </li>
            <li>
              <b>Rotate to every dragon</b> with 30s+ warning — target 1.3 dragon
              takedowns/game (his win-rate level).
            </li>
            <li>
              <b>Two hard stops:</b> log off after 3 losses; no ranked after midnight.
            </li>
            <li>
              <b>Ward lane bushes by 2:30</b> and avoid the pre-10-min death — cut
              early-death games from {A.deaths.pctGamesEarlyDeath}% toward 50%.
            </li>
            <li>
              <b>Counter-pick discipline:</b> Caitlyn only into her good matchups; Miss
              Fortune into Kai&apos;Sa / Jinx / Sivir / Zeri.
            </li>
            <li>
              <b>Convert leads:</b> when ahead at 14 min, group for plates + dragon
              instead of farming side lane.
            </li>
            <li>
              <b>Buy a control ward every back</b> (0.45/game now vs 0.71 for peers).
            </li>
            <li>
              <b>Ladder in the 8–9&nbsp;PM window</b> when possible.
            </li>
          </ol>
          <div className="callout win">
            <h3>Expected impact</h3>
            <p>
              The Sivir cut, matchup discipline, and two scheduling rules each target
              5–13 point win-rate swings on meaningful samples. Even partial adoption
              should move him from 51.5% toward 54–55% — enough to climb out of Diamond III.
            </p>
          </div>
        </section>

        <footer>
          <p>
            <b>Methodology:</b> {S.nGames} ranked-solo games + frame-by-frame timelines
            from the Riot Match-V5 API, benchmarked against {B.n} ADC performances sampled
            from {120} Diamond-ladder players. Effect size = Cohen&apos;s d. Small-sample
            champs/matchups (&lt;10 games) are directional only. Local time inferred, not
            from client. Generated from his own data — see the full written report and code
            on GitHub.
          </p>
        </footer>
      </div>
    </>
  );
}

// ---- small data helpers (server-side, run at build) ----
function champPct(name) {
  const c = A.champions.find((x) => x.champion === name);
  return c ? c.share : 0;
}
function sivir() {
  return A.champions.find((x) => x.champion === "Sivir") || { games: 0, wr: 0 };
}
function streak(label) {
  const b = A.time.byStreak.find((x) => x.bucket === label);
  return b ? b.wr : "?";
}
function hour(h) {
  const b = A.time.byHour.find((x) => Number(x.bucket) === h);
  return b ? b.wr : "?";
}
function hourGames(h) {
  const b = A.time.byHour.find((x) => Number(x.bucket) === h);
  return b ? b.games : 0;
}
function wlDragon() {
  const r = A.winLoss.find((x) => x.key === "dragonTakedowns");
  return r ? `${r.winMean} vs ${r.lossMean}` : "";
}
