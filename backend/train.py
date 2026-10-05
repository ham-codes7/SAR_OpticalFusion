"""Train the change detectors (one per phenomenon x input variant) and write a model card.

    python train.py                 # everything
    python train.py urban           # just one phenomenon, merged into the model card

Labels come from Impact Observatory annual land cover (2017 -> 2023). Each
region is split into 64-pixel blocks; a quarter of the blocks are held out and
never trained on. Every region is used twice: once clear, once with synthetic
cloud over the optical image, so the fused models learn to lean on SAR.
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
RNG = np.random.default_rng(11)


def fetch(bbox):
    b = scenes.load_scene(bbox, *regions.BEFORE)
    a = scenes.load_scene(bbox, *regions.AFTER)
    return b, a, scenes.load_landcover(bbox, YEARS[0]), scenes.load_landcover(bbox, YEARS[1])


def test_blocks(shape, idx):
    rows, cols = np.indices(shape) // 64
    return ((rows * 7 + cols * 13 + idx * 5) % 4 == 0).ravel()


def condition(b, a, cloudy, seed):
    opt_b, opt_a = b["opt"], a["opt"]
    if cloudy:
        shape = opt_a.shape[1:]
        opt_a = scenes.apply_cloud(opt_a, scenes.simulate_cloud(shape, CLOUD_AFTER, seed))
        opt_b = scenes.apply_cloud(opt_b, scenes.simulate_cloud(shape, CLOUD_BEFORE, seed + 100))
    return opt_b, opt_a


def main():
    t0 = time.time()
    card = {"labels": f"Impact Observatory 10 m annual land cover, {YEARS[0]} -> {YEARS[1]}", "model": "HistGradientBoostingClassifier (scikit-learn)", "model_params": detect.MODEL_PARAMS,
            "cloud_test_fraction": CLOUD_AFTER, "phenomena": {}}
    detect.MODEL_DIR.mkdir(exist_ok=True)
    card_path = detect.MODEL_DIR / "model_card.json"
    if card_path.exists():
        card["phenomena"] = json.loads(card_path.read_text())["phenomena"]
    for phen in sys.argv[1:] or detect.PHENOMENA:
        boxes = regions.TRAINING[phen]
        with ThreadPoolExecutor(4) as ex:
            loaded = list(ex.map(fetch, boxes))
        print(f"[{phen}] data ready for {len(boxes)} regions ({time.time() - t0:.0f}s)", flush=True)
        card["phenomena"][phen] = {"regions": boxes, "variants": {}}
        for variant in detect.VARIANTS:
            xs, ys, evals = [], [], []
            for idx, (b, a, lc0, lc1) in enumerate(loaded):
                ref, known = detect.reference_change(phen, lc0, lc1)
                y, known_f, test = ref.ravel(), known.ravel(), test_blocks(ref.shape, idx)
                for cloudy in (False, True):
                    opt_b, opt_a = condition(b, a, cloudy, idx)
                    sb = detect.variant_stack(variant, opt_b, b["sar"])
                    sa = detect.variant_stack(variant, opt_a, a["sar"])
                    x, valid = detect.features(sb, sa)
                    pool = valid & known_f & ~test
                    pos = np.flatnonzero(pool & y)
                    neg = np.flatnonzero(pool & ~y)
                    pos = RNG.choice(pos, min(len(pos), 4000), replace=False)
                    neg = RNG.choice(neg, min(len(neg), 3 * max(len(pos), 500)), replace=False)
                    take = np.concatenate([pos, neg])
                    xs.append(x[take].astype("float32"))
                    ys.append(y[take])
                    evals.append((cloudy, x, valid, y, known_f & test, known_f & ~test, ref.shape))
            model = detect.new_model().fit(np.concatenate(xs), np.concatenate(ys))
            probs = []
            for cloudy, x, valid, y, scored, tune, shape in evals:
                prob = np.zeros(len(y), "float32")
                prob[valid] = model.predict_proba(x[valid])[:, 1]
                probs.append(prob.reshape(shape))

            def f1_at(thr, cond, which):
                tp = fp = fn = 0
                for prob, (cloudy, _, _, y, scored, tune, _) in zip(probs, evals):
                    if cond is not None and cloudy != cond:
                        continue
                    sel = scored if which == "test" else tune
                    mask = detect.to_mask(prob, thr).ravel()
                    tp += int((mask & y & sel).sum())
                    fp += int((mask & ~y & sel).sum())
                    fn += int((~mask & y & sel).sum())
                p = tp / (tp + fp) if tp + fp else 0.0
                r = tp / (tp + fn) if tp + fn else 0.0
                return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r) if p + r else 0.0, 3)}

            # cut-off tuned on the training blocks only, then scored on the held-out blocks
            threshold = max(np.arange(0.3, 0.91, 0.05), key=lambda t: f1_at(t, None, "tune")["f1"])
            threshold = float(round(threshold, 2))
            joblib.dump({"model": model, "threshold": threshold}, detect.MODEL_DIR / f"{phen}_{variant}.joblib", compress=3)
            scores = {"clear": f1_at(threshold, False, "test"), "cloudy": f1_at(threshold, True, "test")}
            card["phenomena"][phen]["variants"][variant] = {"train_pixels": int(sum(len(v) for v in ys)), "threshold": threshold, **scores}
            print(f"  {variant:8s} thr {threshold:.2f}  clear F1 {scores['clear']['f1']:.3f}   cloudy F1 {scores['cloudy']['f1']:.3f}   ({time.time() - t0:.0f}s)", flush=True)
        card_path.write_text(json.dumps(card, indent=2))
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
