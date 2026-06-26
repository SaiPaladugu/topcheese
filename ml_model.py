"""
'The Algorithm' — train a logistic-regression model on his ranked games to predict
WIN from his controllable behavior, then:
  - report honest (k-fold) accuracy + AUC
  - rank standardized coefficients = "what the algorithm blames"
  - find the game he most DESERVED to win but lost, and the one he most got CARRIED in
  - counterfactual: predicted WR if he fixed deaths / KP to Diamond average
Pure numpy. Writes analysis.json["ml"].
"""
import os
import csv
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(HERE, "data", "processed")

FEATURES = [
    ("deaths", "Deaths"), ("deadPct", "Time dead %"), ("killParticipation", "Kill participation"),
    ("teamDmgPct", "Team damage %"), ("goldDiff14", "Gold lead @14"),
    ("csDiff14", "CS lead @14"), ("csPerMin", "CS / min"),
    ("visionPerMin", "Vision / min"), ("controlWards", "Control wards"),
    ("soloKills", "Solo kills"), ("laneMinions10", "Lane CS @10"),
    ("dmgPerMin", "Damage / min"), ("goldPerMin", "Gold / min"),
    ("turretPlates", "Turret plates"),
]


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def fit(X, y, l2=1.0, iters=4000, lr=0.3):
    n, d = X.shape
    w = np.zeros(d); b = 0.0
    for _ in range(iters):
        p = sigmoid(X @ w + b)
        gw = X.T @ (p - y) / n + l2 * w / n
        gb = np.mean(p - y)
        w -= lr * gw; b -= lr * gb
    return w, b


def auc(y, p):
    pos = p[y == 1]; neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    # rank-based AUC
    allp = np.concatenate([pos, neg])
    order = allp.argsort()
    ranks = np.empty_like(order, float); ranks[order] = np.arange(1, len(allp) + 1)
    r_pos = ranks[:len(pos)].sum()
    return (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def main():
    rows = []
    with open(os.path.join(PROC, "ranked_solo.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    keys = [k for k, _ in FEATURES]
    raw = []
    y = []
    meta = []
    for r in rows:
        vals = []
        ok = True
        for k in keys:
            try:
                vals.append(float(r[k]))
            except (ValueError, TypeError):
                vals.append(np.nan)
        raw.append(vals)
        y.append(int(r["win"]))
        meta.append({"champ": r["champion"], "win": int(r["win"]),
                     "deaths": r["deaths"], "kp": r["killParticipation"],
                     "g14": r["goldDiff14"], "date": r["date"], "matchId": r["matchId"]})
    X = np.array(raw, float)
    y = np.array(y, float)
    # impute column means
    col_mean = np.nanmean(X, axis=0)
    inds = np.where(np.isnan(X))
    X[inds] = np.take(col_mean, inds[1])
    # standardize
    mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1
    Xs = (X - mu) / sd

    # k-fold CV
    rng = np.random.default_rng(7)
    idx = rng.permutation(len(y))
    folds = np.array_split(idx, 5)
    accs, aucs = [], []
    for i in range(5):
        te = folds[i]; tr = np.concatenate([folds[j] for j in range(5) if j != i])
        w, b = fit(Xs[tr], y[tr])
        p = sigmoid(Xs[te] @ w + b)
        accs.append(np.mean((p >= 0.5) == y[te]))
        a = auc(y[te], p)
        if a is not None:
            aucs.append(a)

    # final model on all data
    w, b = fit(Xs, y)
    p_all = sigmoid(Xs @ w + b)

    coefs = sorted(
        [{"key": k, "label": lbl, "coef": round(float(w[i]), 3),
          "odds": round(float(np.exp(w[i])), 2)}
         for i, (k, lbl) in enumerate(FEATURES)],
        key=lambda c: abs(c["coef"]), reverse=True)

    # only "real" games (had a 14-min timeline + >=20 min) so remakes don't pollute picks
    real = set()
    for i, r in enumerate(rows):
        try:
            if r["goldDiff14"] != "" and float(r["durationMin"]) >= 20:
                real.add(i)
        except (ValueError, TypeError):
            pass
    losses = [(i, p_all[i]) for i in range(len(y)) if y[i] == 0 and i in real]
    wins = [(i, p_all[i]) for i in range(len(y)) if y[i] == 1 and i in real]
    threw_i = max(losses, key=lambda t: t[1])[0]
    carried_i = min(wins, key=lambda t: t[1])[0]

    def gmeta(i):
        m = meta[i]
        return {"champ": m["champ"], "deaths": m["deaths"], "kp": round(float(m["kp"]), 1) if m["kp"] else None,
                "g14": m["g14"], "predWin": round(float(p_all[i]) * 100, 1), "matchId": m["matchId"]}

    A = json.load(open(os.path.join(PROC, "analysis.json"), encoding="utf-8"))
    # intuitive counterfactual: predicted WR if he played every game like his
    # average WIN vs his average LOSS (feature profiles)
    def predict_profile(mask):
        prof = X[mask].mean(0)
        return round(float(sigmoid(((prof - mu) / sd) @ w + b)) * 100, 1)
    like_win = predict_profile(y == 1)
    like_loss = predict_profile(y == 0)

    ml = {
        "features": len(FEATURES),
        "nGames": int(len(y)),
        "cvAccuracy": round(float(np.mean(accs)) * 100, 1),
        "cvAuc": round(float(np.mean(aucs)), 3),
        "coefs": coefs,
        "threw": gmeta(threw_i),
        "carried": gmeta(carried_i),
        "playLikeWin": like_win,
        "playLikeLoss": like_loss,
    }
    A["ml"] = ml
    json.dump(A, open(os.path.join(PROC, "analysis.json"), "w", encoding="utf-8"), indent=2)
    print(f"CV acc {ml['cvAccuracy']}%  AUC {ml['cvAuc']}  (n={ml['nGames']})")
    print("top blames:", [(c['label'], c['coef']) for c in coefs[:6]])
    print("threw:", ml["threw"])
    print("carried:", ml["carried"])
    print("play like win:", ml["playLikeWin"], "| like loss:", ml["playLikeLoss"])


if __name__ == "__main__":
    main()
