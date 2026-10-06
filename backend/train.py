"""Train the change detectors (one per phenomenon x input variant) and write a model card.

    python train.py                 # everything
    python train.py urban           # just one phenomenon, merged into the model card

Labels: Hansen Global Forest Change for forest loss; Impact Observatory annual land
cover for urban growth. Scores are leave-region-out:
the regions are split into five folds, each fold is predicted by a model that never
saw it, and the cut-off is chosen on those unseen-region predictions. The final model
is then trained on every region and also scored on the app presets, which are never
trained on. Every region is used twice, once clear and once with synthetic cloud over
the optical image, so the fused models learn to lean on radar.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import joblib
import numpy as np

from app import detect, regions, scenes

CLOUD_AFTER, CLOUD_BEFORE = 0.35, 0.15
YEARS = (detect.reference_year(*regions.BEFORE), detect.reference_year(*regions.AFTER))
FOLDS = 5
THRESHOLDS = np.round(np.arange(0.3, 0.96, 0.05), 2)
RNG = np.random.default_rng(11)


def fetch(phen, bbox):
    b = scenes.load_scene(bbox, *regions.BEFORE)
    a = scenes.load_scene(bbox, *regions.AFTER)
    ref, known = scenes.load_reference(bbox, phen, *YEARS)
    return b, a, ref.ravel(), known.ravel(), ref.shape


def features(variant, region, cloudy, seed):
    b, a, *_ = region
    opt_b, opt_a = b["opt"], a["opt"]
    if cloudy:
        shape = opt_a.shape[1:]
        opt_a = scenes.apply_cloud(opt_a, scenes.simulate_cloud(shape, CLOUD_AFTER, seed))
        opt_b = scenes.apply_cloud(opt_b, scenes.simulate_cloud(shape, CLOUD_BEFORE, seed + 100))
    return detect.features(detect.variant_stack(variant, opt_b, b["sar"]), detect.variant_stack(variant, opt_a, a["sar"]))


def sample(x, valid, y, known):
    pool = valid & known
    pos = np.flatnonzero(pool & y)
    neg = np.flatnonzero(pool & ~y)
    pos = RNG.choice(pos, min(len(pos), 4000), replace=False)
    neg = RNG.choice(neg, min(len(neg), 3 * max(len(pos), 500)), replace=False)
    take = np.concatenate([pos, neg])
    return x[take], y[take]


def counts(model, x, valid, y, known, shape):
    """tp, fp, fn at every candidate cut-off."""
    prob = np.full(len(y), np.nan, "float32")
    if valid.any():
        prob[valid] = model.predict_proba(x[valid])[:, 1]
    prob = prob.reshape(shape)
    out = {}
    for t in THRESHOLDS:
        m = detect.to_mask(prob, t).ravel()
        out[t] = np.array([(m & y & known).sum(), (m & ~y & known).sum(), (~m & y & known).sum()])
    return out


def scores(c):
    tp, fp, fn = (int(v) for v in c)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r) if p + r else 0.0, 3)}


def add(total, c):
    for t in THRESHOLDS:
        total[t] = total.get(t, 0) + c[t]


def train_variant(variant, train, tests):
    t0 = time.time()
    samples = {}
    for i, region in enumerate(train):
        for cloudy in (False, True):
            x, valid = features(variant, region, cloudy, i)
            samples[i, cloudy] = sample(x, valid, region[2], region[3])

    def fit(idx):
        keys = [k for k in samples if k[0] in idx]
        return detect.new_model().fit(np.concatenate([samples[k][0] for k in keys]), np.concatenate([samples[k][1] for k in keys]))

    unseen = {False: {}, True: {}}
    folds = [i % FOLDS for i in range(len(train))]
    for f in range(FOLDS):
        model = fit([i for i in range(len(train)) if folds[i] != f])
        for i in (i for i in range(len(train)) if folds[i] == f):
            for cloudy in (False, True):
                add(unseen[cloudy], counts(model, *features(variant, train[i], cloudy, i), *train[i][2:]))
    threshold = float(max(THRESHOLDS, key=lambda t: scores(unseen[False][t] + unseen[True][t])["f1"]))

    model = fit(range(len(train)))
    joblib.dump({"model": model, "threshold": threshold}, detect.MODEL_DIR / f"{PHEN}_{variant}.joblib", compress=3)
    presets = {False: {}, True: {}}
    for j, region in enumerate(tests):
        for cloudy in (False, True):
            add(presets[cloudy], counts(model, *features(variant, region, cloudy, 50 + j), *region[2:]))
    entry = {
        "train_pixels": int(sum(len(v[1]) for v in samples.values())),
        "threshold": threshold,
        "clear": scores(unseen[False][threshold]),
        "cloudy": scores(unseen[True][threshold]),
        "presets": {"clear": scores(presets[False][threshold]), "cloudy": scores(presets[True][threshold])},
    }
    print(f"  {variant:8s} thr {threshold:.2f}  unseen F1 {entry['clear']['f1']:.3f} / {entry['cloudy']['f1']:.3f}"
          f"   presets F1 {entry['presets']['clear']['f1']:.3f} / {entry['presets']['cloudy']['f1']:.3f}   ({time.time() - t0:.0f}s)", flush=True)
    return entry


def main():
    global PHEN
    detect.MODEL_DIR.mkdir(exist_ok=True)
    card_path = detect.MODEL_DIR / "model_card.json"
    for PHEN in sys.argv[1:] or detect.PHENOMENA:
        boxes = regions.TRAINING[PHEN]
        test_boxes = [p["bbox"] for p in regions.PRESETS if p["phenomenon"] == PHEN]
        with ThreadPoolExecutor(4) as ex:
            train = list(ex.map(lambda bb: fetch(PHEN, bb), boxes))
            tests = list(ex.map(lambda bb: fetch(PHEN, bb), test_boxes))
        print(f"[{PHEN}] data ready: {len(train)} training regions, {len(tests)} presets", flush=True)
        variants = {v: train_variant(v, train, tests) for v in detect.VARIANTS}
        card = json.loads(card_path.read_text()) if card_path.exists() else {"phenomena": {}}
        card.update({
            "labels": {"deforestation": "Hansen Global Forest Change v1.12 (Landsat, 30 m), loss years after the before date up to the after date",
                       "urban": "Impact Observatory 10 m annual land cover, not built -> built"},
            "years": list(YEARS),
            "pixel_m": scenes.data.PIXEL_M,
            "model": "HistGradientBoostingClassifier (scikit-learn)",
            "model_params": detect.MODEL_PARAMS,
            "evaluation": f"leave-region-out, {FOLDS} folds; 'clear'/'cloudy' are unseen-region scores, 'presets' are the app presets (never trained on)",
            "cloud_test_fraction": CLOUD_AFTER,
        })
        card["phenomena"][PHEN] = {"regions": boxes, "variants": variants}
        card_path.write_text(json.dumps(card, indent=2))


if __name__ == "__main__":
    main()
