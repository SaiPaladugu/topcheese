import A from "../data/analysis.json";

const S = A.summary;
const B = A.benchmark;
const D = A.duo;

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
          <h1>Topcheese044 — Solo Queue Intervention 🤡</h1>
          <p className="sub">
            {S.nGames} games of a chud farming minions instead of farming a calorie deficit ·{" "}
            {S.dateFrom} → {S.dateTo} · {S.rank} · ADC (allegedly) · BMI (classified)
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
          <a href="#duo">The Calatis effect</a>
          <a href="#form">Form</a>
          <a href="#plan">Action plan</a>
        </nav>

        {/* ---------- DIAGNOSIS ---------- */}
        <section id="diagnosis">
          <h2>The diagnosis: a passive farming chud who refuses to impact the game</h2>
          <p className="lead">
            Benchmarked against {B.n} real Diamond ADCs who actually press their abilities
            on enemy champions, this NPC is statistically average at everything — with one
            consistent personality trait: he farms safe and refuses to do anything that
            involves risk, courage, or a single ounce of agency — much like his refusal to
            do a single ounce of cardio.
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
          <Chart src="/charts/benchmark.png" cap="Him vs real Diamond ADCs (100 = at rank average). All that red = the chud underperforming his own rank." />
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
            <h3>Translation for the NPC</h3>
            <p>
              He is not hardstuck because of his mechanics — he wins lane on CS and avoids
              dying. He is hardstuck because he plays the entire mid-game like a very polite
              spectator. Good news, gooner: a coward problem climbs faster than a bad-hands
              problem, so you actually have a path out of this if you grow a spine — and,
              ideally, shrink a waistline.
            </p>
          </div>
        </section>

        {/* ---------- WHAT DECIDES GAMES ---------- */}
        <section id="decide">
          <h2>What actually decides his games (not his mechanics, lol)</h2>
          <p className="lead">
            Every metric compared between his wins and losses, ranked by effect size
            (Cohen&apos;s d). Ignoring KDA (a scoreboard echo for chuds who think KDA is a
            personality), the controllable differences are objective presence and gold
            conversion — both bigger than the laning he won&apos;t shut up about, and both
            smaller than his pant size.
          </p>
          <Chart src="/charts/winloss_effect.png" cap="What separates his wins from losses. Spoiler: it's showing up to objectives, which he doesn't." />
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
          <Chart src="/charts/lane14_winloss.png" cap="Lane lead at 14 minutes: wins vs losses. He gets the lead and then squanders it." />
          <div className="callout win">
            <h3>The headline this chud needs tattooed</h3>
            <p>
              Objective presence (dragon takedowns: {wlDragon()}) and gold conversion matter
              MORE than laning — and he already wins lane. The leak is 100% between his ears:
              he gets a lead and then does absolutely nothing with it. A lead is wasted on
              this man. Walk to the dragon, NPC — and then keep walking, for the cardio.
            </p>
          </div>
        </section>

        {/* ---------- CHAMPIONS ---------- */}
        <section id="champs">
          <h2>The champion pool (aka the Caitlyn comfort blanket)</h2>
          <p className="lead">
            {champPct("Caitlyn")}% Caitlyn, because heaven forbid the chud learn a second
            character. His actual best high-volume champ is Miss Fortune — which he plays
            half as much as his worst champ, Sivir. NPC behavior — and his champ pool, like
            his portion sizes, badly needs trimming.
          </p>
          <Chart src="/charts/champion_wr.png" cap="Win rate by champion (≥10 games). The line is his 51.5% average — note how many bars are below the chud's own mediocrity." />
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
            <h3>The Sivir crime scene</h3>
            <p>
              {sivir().games} games at {sivir().wr}% — his BEST CS/min yet his WORST win
              rate. The textbook signature of a chud who farms gorgeously and contributes
              nothing. He stared at a 40% win rate {sivir().games} separate times and went
              &quot;run it back.&quot; Swapping those griefs for his ~53% champs is worth
              ~+9 wins, or as he calls it, &quot;variance&quot; — the same word he uses for
              his weight.
            </p>
          </div>
        </section>

        {/* ---------- MATCHUPS ---------- */}
        <section id="matchups">
          <h2>Matchups — pick Caitlyn on purpose, not on autopilot, chud</h2>
          <p className="lead">
            Caitlyn&apos;s win rate swings wildly by enemy ADC, and this gooner locks her
            blind every single game because reading the enemy comp would mean looking up
            from his own minimap. Into her bad matchups, lock Miss Fortune. He won&apos;t —
            same energy as the gym membership he keeps renewing and never using.
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
            Enemy ADCs that beat this chud no matter what he picks
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
          <h2>Tilt &amp; scheduling — the chud cannot stop himself</h2>
          <p className="lead">
            When this LTN plays is half his problem; what he&apos;s snacking on while he
            plays is the other half. Local time inferred from his sleep-deprived activity
            pattern as UTC{A.time.inferredUtcOffset} (US Central).
          </p>
          <div className="grid2">
            <div className="callout loss">
              <h3>🛑 Log off after 3 losses, LTN</h3>
              <p>
                His win rate craters to {streak("after 3+ losses")}% after three straight
                losses — his brain is soup and he queues anyway. Every game past that is a
                donation to the enemy team, much like every late-night snack is a donation
                to the gut.
              </p>
            </div>
            <div className="callout loss">
              <h3>🌙 No ranked after midnight, gooner</h3>
              <p>
                Midnight–1&nbsp;AM runs {hour(0)}–{hour(1)}% over {hourGames(0) + hourGames(1)}{" "}
                games — and midnight is his single most-played hour. He&apos;s gooner-queueing
                into the void at 1&nbsp;AM with one eye open and one hand in the chip bag.
                His good window (8–9&nbsp;PM) is {hour(20)}–{hour(21)}% — the other good
                window is called &quot;the gym, in the morning.&quot;
              </p>
            </div>
          </div>
          <Chart src="/charts/streak_wr.png" cap="Win rate by streak state — the chud tilts and keeps queueing anyway." />
          <Chart src="/charts/hour_wr.png" cap="Win rate by hour. Functional at 8 PM, fully cooked by 1 AM." />
          <Chart src="/charts/gamesperday_wr.png" cap="Win rate by games per day (short days look bad partly because he ragequits after losing)." />
        </section>

        {/* ---------- THE CALATIS EFFECT ---------- */}
        <section id="duo">
          <h2>The Calatis effect — can the duo carry this chud?</h2>
          <p className="lead">
            He&apos;s queued up with <b>Calatis</b> {D.sharedGamesAnyQueue} times across{" "}
            {D.accounts.length} alt accounts ({D.accounts.map((a) => a.id).join(", ")}).
            Restricting to ranked solo/duo for a fair read: the verdict is that not even his
            friend can drag this NPC up the ladder.
          </p>
          <div className="cards">
            <div className="card">
              <div className="k">WR duo&apos;d with Calatis</div>
              <div className={"v " + (D.together.wr >= D.alone.wr ? "good" : "bad")}>
                {D.together.wr}%
              </div>
              <div className="k">{D.together.games} ranked games</div>
            </div>
            <div className="card">
              <div className="k">WR without Calatis</div>
              <div className="v">{D.alone.wr}%</div>
              <div className="k">{D.alone.games} ranked games</div>
            </div>
            <div className="card">
              <div className="k">Net effect of the duo</div>
              <div className={"v " + (D.together.wr - D.alone.wr >= 0 ? "good" : "bad")}>
                {(D.together.wr - D.alone.wr).toFixed(1)}%
              </div>
              <div className="k">friendship is not a win condition</div>
            </div>
            <div className="card">
              <div className="k">Calatis&apos; own KDA / KP</div>
              <div className="v good">
                {D.calatisSelf.kda} / {D.calatisSelf.kp}%
              </div>
              <div className="k">
                vs his {D.hisStatsAlone.kda} / {D.hisStatsAlone.kp}% — the jungler does more
              </div>
            </div>
          </div>

          <h3 style={{ margin: "24px 0 4px 2px", fontSize: 17 }}>
            Same friend, different account, opposite results
          </h3>
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Calatis account</th>
                  <th className="num">Games</th>
                  <th className="num">His WR duo&apos;d</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {D.perAccount.map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>
                    <td className="num">{a.games}</td>
                    <td className="num">
                      <span className={"pill " + wrClass(a.wr)}>{a.wr}%</span>
                    </td>
                    <td>
                      <span className={"pill " + (a.wr >= 51.5 ? "good" : "bad")}>
                        {a.wr >= 51.5 ? "win condition ✅" : "anchor ❌"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="lead" style={{ marginTop: 14 }}>
            His most-played Calatis account ({D.perAccount[0].id}, {D.perAccount[0].games}{" "}
            games) is a {D.perAccount[0].wr}% grief — and he keeps re-queueing with it anyway.
            Calatis is a jungle/mid main (
            {Object.keys(D.calatisRoles)
              .slice(0, 2)
              .map((r) => r.toLowerCase())
              .join(" / ")}
            ), mostly on {D.calatisChamps.slice(0, 3).map((c) => c[0]).join(", ")}.
          </p>

          <h3 style={{ margin: "24px 0 4px 2px", fontSize: 17 }}>
            Does Calatis change how he plays? No. He&apos;s a chud either way.
          </h3>
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>His stat</th>
                  <th className="num">With Calatis</th>
                  <th className="num">Without</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["KDA", "kda"],
                  ["CS / min", "csPerMin"],
                  ["Kill participation %", "kp"],
                  ["Team damage %", "teamDmgPct"],
                  ["Deaths", "deaths"],
                  ["Dragon takedowns", "dragonTakedowns"],
                ].map(([label, k]) => (
                  <tr key={k}>
                    <td>{label}</td>
                    <td className="num">{D.hisStatsTogether[k]}</td>
                    <td className="num">{D.hisStatsAlone[k]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="callout loss">
            <h3>It&apos;s not the teammates — it&apos;s the chud</h3>
            <p>
              Identical. The passive-farming-chud personality is load-bearing and travels with
              him. Worse: <b>Calatis is statistically the better player.</b> From the jungle/mid
              (Jarvan, Zoe, Nidalee), Calatis posts a <b>5.19 KDA</b> and <b>55.5% kill
              participation</b> — while topcheese sits bot at <b>44% KP</b> and a feather-light{" "}
              <b>23% damage share</b> — and they <i>still</i> only scrape 50%. When your friend
              is hard-carrying you to a coin flip, the leak was never the duo. It was the chud in
              the bot lane who should be running it back on a treadmill.
            </p>
          </div>
        </section>

        {/* ---------- FORM ---------- */}
        <section id="form">
          <h2>Two-year form: a plateau (and not the only thing that&apos;s plateaued)</h2>
          <p className="lead">
            Rolling 50-game win rate has bounced around 50% for two straight years — that&apos;s
            not a plateau, it&apos;s a lifestyle, much like the cardio he&apos;s been meaning to
            start. Breaking it means raising the flagged metrics above and possibly his heart
            rate above resting for once.
          </p>
          <Chart src="/charts/form.png" cap="Rolling 50-game win rate over time — flatter than the treadmill he never uses." />
        </section>

        {/* ---------- PLAN ---------- */}
        <section id="plan">
          <h2>The intervention plan (read it twice, NPC)</h2>
          <ol className="plan">
            <li>
              <b>Delete Sivir.</b> Default to Caitlyn / Miss Fortune. ~+9 wins for the low
              price of self-awareness — and while you&apos;re deleting things, delete the
              third snack.
            </li>
            <li>
              <b>Walk to every dragon</b> with 30s+ warning — target 1.3 takedowns/game.
              The drake is the big lizard, mid is that way, and the walk counts as steps.
            </li>
            <li>
              <b>Two hard stops:</b> log off after 3 losses; no ranked after midnight — use
              the spare time to see a squat rack.
            </li>
            <li>
              <b>Ward the bush by 2:30</b> and skip the minute-7 suicide — drag early-death
              games from {A.deaths.pctGamesEarlyDeath}% toward 50%, and drag yourself onto a
              treadmill.
            </li>
            <li>
              <b>Counter-pick discipline:</b> Caitlyn only into her good matchups; Miss
              Fortune into Kai&apos;Sa / Jinx / Sivir / Zeri. Cut the weight off your champ
              pool and, frankly, off you.
            </li>
            <li>
              <b>Use your leads:</b> when ahead at 14, group for plates + drake instead of
              solo-farming a side lane like an LTN — calories aren&apos;t the only thing
              worth burning.
            </li>
            <li>
              <b>Buy a control ward every back</b> (0.45/game now vs 0.71 for actual
              Diamonds). It&apos;s 75 gold, gooner — roughly one skipped energy drink.
            </li>
            <li>
              <b>Ladder at 8–9&nbsp;PM</b> when his brain is online. Morning slot&apos;s
              open for a run.
            </li>
          </ol>
          <div className="callout win">
            <h3>Expected impact</h3>
            <p>
              The Sivir cut, matchup discipline, and two scheduling rules each target 5–13
              point swings on real samples. Even half-effort moves him from 51.5% toward
              54–55% — out of Diamond III and into a tier where he can disappoint fresh
              people. The diet&apos;s on him, but the math says shed both the Sivir games and
              a few pounds.
            </p>
          </div>
        </section>

        <footer>
          <p>
            <b>Methodology (the one nice paragraph):</b> {S.nGames} ranked-solo games +
            frame-by-frame timelines from the Riot Match-V5 API, benchmarked against {B.n}{" "}
            ADC performances sampled from {120} Diamond-ladder players. Effect size =
            Cohen&apos;s d. Small-sample champs/matchups (&lt;10 games) are directional only.
            Local time inferred, not from client. Every insult is affectionate and every
            number is real — which is the funniest possible combination. Now go for a jog.
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
