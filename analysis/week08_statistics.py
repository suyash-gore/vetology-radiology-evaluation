"""Week 8 statistical analysis for the Vetology radiology-report evaluation.

Implements the feasible parts of the approved plan
(Vetology_Research_Knowledge_Base/03_Consolidated_Knowledge_Base/
08_Research_Design_and_Analysis_Plan.md, section 6).

Inputs (NOT in the repository; confidential, owner-supplied):
    --bundle  path to the extracted ``files-bundle-01`` directory that holds
              the source/reference workbooks and prediction JSONL files.
Outputs (aggregate statistics only; no case-level data, no report text):
    --out-md    Markdown results file
    --out-json  JSON results file

Determinism: one bootstrap index matrix is drawn from
``numpy.random.default_rng(SEED)``. The same resampled reports are used for
every evaluation, so paired comparisons on the same cases are genuinely
paired. Re-running with the same inputs gives identical output.

Usage:
    python analysis/week08_statistics.py --bundle <path>/files-bundle-01 \
        --out-md  Vetology_Research_Knowledge_Base/04_Evidence_and_Artifacts/07_Statistical_Analysis_Results.md \
        --out-json Vetology_Research_Knowledge_Base/04_Evidence_and_Artifacts/07_statistical_results.json

Requires: numpy, openpyxl (openpyxl is pinned in requirements.txt; numpy is
an analysis-only dependency).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openpyxl

SEED = 20261128
B = 10_000
Z = 1.959963984540054  # two-sided 95%

CT_M1 = "Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx"
CT_GS = "1_canine_thorax_gold_standard_score_draft.xlsx"
FT_M1 = "2_feline_thorax_raw_data_encoded.xlsx"
FT_GS = "2_feline_thorax_gold_standard_score_draft.xlsx"
CA_M1 = "3_canine_abdomen_raw_data_encoded.xlsx"
CA_GS = "3_canine_abdomen_gold_standard_score_draft.xlsx"
G7 = "outputs/week_07/week 5 rebuild with different llm (gemini flash)/"
FTD = "outputs/week_07/2nd application/feline_thorax/predictions/predictions.jsonl"
CAD = "outputs/week_07/3rd application/canine_abdomen/predictions/predictions.jsonl"
FT_NORM = {"pulmonary_nodules", "esophagitis", "pneumonia"}
REPORT_FIELDS = (
    "Findings (original radiologist report)",
    "Conclusions (original radiologist report)",
    "Recommendations (original radiologist report)",
)

# Registered evaluations (IDs from 04_Evidence_and_Artifacts/03_..._Register.md).
# expected = registered micro TP, FN, TN, FP (verified against workbooks in W8).
EVALS = {
    "EVAL-01": dict(ds="CT", matrix="M1", label="CT Week 4 OpenAI M1", run="RUN-02",
                    pred="outputs/week_04/matrix_1/predictions.jsonl", ref=CT_M1, expected=(128, 921, 913, 38)),
    "EVAL-02": dict(ds="CT", matrix="M2", label="CT Week 4 OpenAI M2", run="RUN-01",
                    pred="outputs/week_04/canine_thorax/predictions.jsonl", ref=CT_GS, expected=(127, 31, 1803, 39)),
    "EVAL-05": dict(ds="CT", matrix="M1", label="CT Week 5 OpenAI M1", run="RUN-03",
                    pred="outputs/week_05/matrix_1/predictions.jsonl", ref=CT_M1, expected=(126, 923, 916, 35)),
    "EVAL-06": dict(ds="CT", matrix="M2", label="CT Week 5 OpenAI M2", run="RUN-04",
                    pred="outputs/week_05/matrix_2/predictions.jsonl", ref=CT_GS, expected=(126, 32, 1806, 36)),
    "EVAL-07": dict(ds="CT", matrix="M1", label="CT Week 7 Gemini M1", run="RUN-05",
                    pred=G7 + "matrix_1/predictions.jsonl", ref=CT_M1, expected=(96, 953, 924, 27)),
    "EVAL-08": dict(ds="CT", matrix="M2", label="CT Week 7 Gemini M2", run="RUN-06",
                    pred=G7 + "matrix_2/predictions.jsonl", ref=CT_GS, expected=(102, 56, 1822, 20)),
    "EVAL-11": dict(ds="FT", matrix="M1", label="FT Week 7 OpenAI M1", run="RUN-07",
                    pred=FTD, ref=FT_M1, norm=True, expected=(29, 505, 1529, 37)),
    "EVAL-12": dict(ds="FT", matrix="M2", label="FT Week 7 OpenAI M2", run="RUN-07",
                    pred=FTD, ref=FT_GS, expected=(58, 59, 1975, 8)),
    "EVAL-13": dict(ds="CA", matrix="M1", label="CA Week 7 OpenAI M1", run="RUN-08",
                    pred=CAD, ref=CA_M1, expected=(34, 246, 697, 23)),
    "EVAL-14": dict(ds="CA", matrix="M2", label="CA Week 7 OpenAI M2", run="RUN-08",
                    pred=CAD, ref=CA_GS, expected=(53, 28, 915, 4)),
}


# --------------------------------------------------------------------- loading
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_workbook_rows(path: Path):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [h for h in rows[0]]
    ci = hdr.index("CaseID")
    pop = [r for r in rows[1:] if r[ci] not in (None, "")][:100]
    return hdr, ci, pop


def load_reference(path: Path, keys, norm=False):
    hdr, ci, pop = load_workbook_rows(path)
    ids, lab = [], []
    for r in pop:
        ids.append(int(r[ci]))
        row = []
        for k in keys:
            v = r[hdr.index(k)]
            v = v.strip() if isinstance(v, str) else v
            if norm and k in FT_NORM:
                v = {"Normal": "Negative", "Abnormal": "Positive"}.get(v, v)
            if v not in ("Positive", "Negative"):
                raise ValueError(f"{path.name}: invalid label {v!r}")
            row.append(1 if v == "Positive" else 0)
        lab.append(row)
    return ids, np.array(lab, dtype=np.int8)


def load_predictions(path: Path):
    recs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") == "success":
            recs[int(r["case_id"])] = r["predictions"]
    return recs


def condition_keys(path: Path):
    """Condition keys = header columns after the 8 report/metadata columns."""
    hdr, _, _ = load_workbook_rows(path)
    return [h for h in hdr[8:] if h]


# --------------------------------------------------------------------- metrics
def counts(y, p):
    tp = ((y == 1) & (p == 1)).sum(axis=-2)
    fn = ((y == 1) & (p == 0)).sum(axis=-2)
    tn = ((y == 0) & (p == 0)).sum(axis=-2)
    fp = ((y == 0) & (p == 1)).sum(axis=-2)
    return tp, fn, tn, fp


def div(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(b > 0, a / np.where(b > 0, b, 1), np.nan)


def rates(tp, fn, tn, fp):
    """Plan section 6.2 definitions. F1 = 2TP/(2TP+FP+FN), undefined only if denominator 0."""
    return dict(
        accuracy=div(tp + tn, tp + fn + tn + fp),
        sensitivity=div(tp, tp + fn),
        specificity=div(tn, tn + fp),
        precision=div(tp, tp + fp),
        f1=div(2 * tp, 2 * tp + fp + fn),
    )


def wilson(x, n):
    if n == 0:
        return None
    p = x / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z / den * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return [max(0.0, c - h), min(1.0, c + h)]


def kappa(a, b):
    a = np.asarray(a).ravel()
    b = np.asarray(b).ravel()
    po = float((a == b).mean())
    pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def mcnemar_exact(bc, cb):
    n = bc + cb
    if n == 0:
        return None
    k = min(bc, cb)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def holm(pvals):
    items = sorted((p, i) for i, p in enumerate(pvals) if p is not None)
    m = len(items)
    adj = [None] * len(pvals)
    running = 0.0
    for rank, (p, i) in enumerate(items):
        running = max(running, min(1.0, (m - rank) * p))
        adj[i] = running
    return adj


def pct_interval(samples):
    s = np.asarray(samples, dtype=float)
    ok = ~np.isnan(s)
    undefined = int((~ok).sum())
    if ok.sum() == 0:
        return None, undefined
    lo, hi = np.percentile(s[ok], [2.5, 97.5])
    return [float(lo), float(hi)], undefined


def r(x, d=6):
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    return round(float(x), d)


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args()
    root = Path(a.bundle)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, 100, size=(B, 100))  # shared report-level resamples

    data, out = {}, {"meta": {}, "evaluations": {}}
    out["meta"] = dict(
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        script="analysis/week08_statistics.py", seed=SEED, bootstrap_replicates=B,
        resampling_unit="report (case); all condition labels of a resampled report kept together",
        interval="percentile 95% over defined replicates; undefined-replicate count reported",
        wilson="95% Wilson score interval per condition (cases treated as independent)",
        f1_definition="2TP/(2TP+FP+FN); undefined only when denominator is 0 (plan section 6.2)",
        inputs={},
    )

    # ---------------- load and verify every evaluation
    for eid, e in EVALS.items():
        refp = root / e["ref"]
        keys = condition_keys(refp)
        ids, y = load_reference(refp, keys, e.get("norm", False))
        preds = load_predictions(root / e["pred"])
        if sorted(ids) != sorted(preds):
            raise SystemExit(f"{eid}: CaseID mismatch")
        p = np.array([[1 if preds[c][k] == "Positive" else 0 for k in keys] for c in ids], dtype=np.int8)
        tp, fn, tn, fp = counts(y, p)
        micro = (int(tp.sum()), int(fn.sum()), int(tn.sum()), int(fp.sum()))
        if micro != e["expected"]:
            raise SystemExit(f"{eid}: counts {micro} != registered {e['expected']}")
        data[eid] = dict(keys=keys, ids=ids, y=y, p=p)
        for f in (e["ref"], e["pred"]):
            out["meta"]["inputs"][f] = sha256(root / f)

    # ---------------- per-evaluation statistics
    for eid, e in EVALS.items():
        d = data[eid]
        y, p, keys = d["y"], d["p"], d["keys"]
        tp, fn, tn, fp = counts(y, p)
        micro_pt = rates(tp.sum(), fn.sum(), tn.sum(), fp.sum())
        cond_pt = rates(tp, fn, tn, fp)
        yb, pb = y[idx], p[idx]  # (B,100,K)
        btp, bfn, btn, bfp = counts(yb, pb)  # (B,K)
        bmicro = rates(btp.sum(1), bfn.sum(1), btn.sum(1), bfp.sum(1))
        bcond = rates(btp, bfn, btn, bfp)  # (B,K)
        res = dict(label=e["label"], dataset=e["ds"], matrix=e["matrix"], run=e["run"],
                   counts=dict(TP=int(tp.sum()), FN=int(fn.sum()), TN=int(tn.sum()), FP=int(fp.sum())),
                   micro={}, macro={}, conditions=[])
        for m in ("accuracy", "sensitivity", "specificity", "precision", "f1"):
            ci, und = pct_interval(bmicro[m])
            res["micro"][m] = dict(point=r(micro_pt[m]), ci95=[r(v) for v in ci] if ci else None,
                                   undefined_replicates=und)
        for m in ("sensitivity", "specificity", "precision", "f1"):
            v = cond_pt[m]
            defined = ~np.isnan(v)
            point = float(np.nanmean(v)) if defined.any() else None
            bm = np.full(B, np.nan)
            any_def = ~np.isnan(bcond[m]).all(1)
            with np.errstate(invalid="ignore"):
                bm[any_def] = np.nanmean(bcond[m][any_def], 1)
            ncontrib = (~np.isnan(bcond[m])).sum(1)
            ci, und = pct_interval(bm)
            res["macro"][m] = dict(point=r(point), included=int(defined.sum()),
                                   excluded_undefined=int((~defined).sum()),
                                   ci95=[r(x) for x in ci] if ci else None, undefined_replicates=und,
                                   contributing_conditions_in_replicates=dict(
                                       min=int(ncontrib.min()), median=float(np.median(ncontrib)),
                                       max=int(ncontrib.max())))
        for j, k in enumerate(keys):
            c = dict(condition=k, TP=int(tp[j]), FN=int(fn[j]), TN=int(tn[j]), FP=int(fp[j]),
                     ref_pos=int(tp[j] + fn[j]), ref_neg=int(tn[j] + fp[j]), pred_pos=int(tp[j] + fp[j]))
            for m, (x, n) in dict(sensitivity=(tp[j], tp[j] + fn[j]), specificity=(tn[j], tn[j] + fp[j]),
                                  precision=(tp[j], tp[j] + fp[j])).items():
                c[m] = dict(point=r(x / n) if n else None, wilson95=[r(v) for v in wilson(int(x), int(n))] if n else None, n=int(n))
            c["f1"] = r(cond_pt["f1"][j])
            c["bootstrap_undefined_replicates"] = {m: int(np.isnan(bcond[m][:, j]).sum())
                                                   for m in ("sensitivity", "precision", "f1")}
            res["conditions"].append(c)
        out["evaluations"][eid] = res

    # ---------------- paired M1 vs M2 (same predictions: FT, CA)
    def paired_diff(e1, e2):
        d1, d2 = data[e1], data[e2]
        assert d1["ids"] == d2["ids"] and d1["keys"] == d2["keys"]
        o = {}
        for lab, (y, p) in (("a", (d1["y"], d1["p"])), ("b", (d2["y"], d2["p"]))):
            o[lab] = rates(*[c.sum(1) for c in counts(y[idx], p[idx])])
            o[lab + "pt"] = rates(*[c.sum() for c in counts(y, p)])
        rr = {}
        for m in ("accuracy", "sensitivity", "specificity", "precision", "f1"):
            ci, und = pct_interval(o["b"][m] - o["a"][m])
            rr[m] = dict(point=r(float(o["bpt"][m] - o["apt"][m])), ci95=[r(v) for v in ci] if ci else None,
                         undefined_replicates=und)
        return rr

    out["paired_reference_contrasts"] = {
        "FT: M2 (EVAL-12) minus M1 (EVAL-11), identical predictions RUN-07": paired_diff("EVAL-11", "EVAL-12"),
        "CA: M2 (EVAL-14) minus M1 (EVAL-13), identical predictions RUN-08": paired_diff("EVAL-13", "EVAL-14"),
    }

    # ---------------- reference-label agreement M1 vs M2 (same cases)
    ref_agree = {}
    for ds, (e1, e2) in {"CT": ("EVAL-01", "EVAL-02"), "FT": ("EVAL-11", "EVAL-12"), "CA": ("EVAL-13", "EVAL-14")}.items():
        d1, d2 = data[e1], data[e2]
        if d1["ids"] != d2["ids"] or d1["keys"] != d2["keys"]:
            ref_agree[ds] = "CaseID or key mismatch; not computed"
            continue
        y1, y2 = d1["y"], d2["y"]
        bk = [kappa(y1[i], y2[i]) for i in idx[:2000]]  # 2,000 replicates suffice for kappa CI
        bk = [x for x in bk if x is not None]
        per = []
        for j, k in enumerate(d1["keys"]):
            per.append(dict(condition=k, agreement=r(float((y1[:, j] == y2[:, j]).mean())),
                            kappa=r(kappa(y1[:, j], y2[:, j])),
                            m1_pos=int(y1[:, j].sum()), m2_pos=int(y2[:, j].sum()),
                            m1_pos_m2_neg=int(((y1[:, j] == 1) & (y2[:, j] == 0)).sum()),
                            m1_neg_m2_pos=int(((y1[:, j] == 0) & (y2[:, j] == 1)).sum())))
        ref_agree[ds] = dict(pairs=int(y1.size), agreement=r(float((y1 == y2).mean())),
                             kappa=r(kappa(y1, y2)),
                             kappa_ci95_cluster_bootstrap_2000=[r(v) for v in np.percentile(bk, [2.5, 97.5])],
                             m1_pos_m2_neg=int(((y1 == 1) & (y2 == 0)).sum()),
                             m1_neg_m2_pos=int(((y1 == 0) & (y2 == 1)).sum()), per_condition=per)
    out["reference_label_agreement"] = ref_agree

    # ---------------- CT model comparison: Week 5 OpenAI vs Week 7 Gemini
    mc = {}
    for mx, (eo, eg) in {"M1": ("EVAL-05", "EVAL-07"), "M2": ("EVAL-06", "EVAL-08")}.items():
        do, dg = data[eo], data[eg]
        assert do["ids"] == dg["ids"] and do["keys"] == dg["keys"]
        y, po, pg = do["y"], do["p"], dg["p"]
        assert (y == dg["y"]).all()
        co, cg = (po == y), (pg == y)
        per, pv = [], []
        for j, k in enumerate(do["keys"]):
            b_ = int((co[:, j] & ~cg[:, j]).sum())
            c_ = int((~co[:, j] & cg[:, j]).sum())
            p = mcnemar_exact(b_, c_)
            pv.append(p)
            per.append(dict(condition=k, openai_only_correct=b_, gemini_only_correct=c_,
                            mcnemar_exact_p=r(p), agreement=r(float((po[:, j] == pg[:, j]).mean())),
                            kappa=r(kappa(po[:, j], pg[:, j]))))
        for item, adj in zip(per, holm(pv)):
            item["holm_p"] = r(adj)
        bk = [kappa(po[i], pg[i]) for i in idx[:2000]]
        bk = [x for x in bk if x is not None]
        mc[mx] = dict(openai=eo, gemini=eg, agreement_pairs=int((po == pg).sum()), pairs=int(po.size),
                      kappa=r(kappa(po, pg)),
                      kappa_ci95_cluster_bootstrap_2000=[r(v) for v in np.percentile(bk, [2.5, 97.5])],
                      testable_conditions=sum(p is not None for p in pv), per_condition=per,
                      paired_difference_gemini_minus_openai=paired_diff(eo, eg))
    out["ct_model_comparison"] = mc

    # ---------------- run-to-run consistency (CT)
    rep = {}
    pairs = {
        "Week 4: RUN-02 (M1 batch) vs RUN-01 (M2 batch)": ("EVAL-01", "EVAL-02"),
        "Week 5: RUN-03 (M1 batch) vs RUN-04 (M2 batch)": ("EVAL-05", "EVAL-06"),
        "Week 7 Gemini: RUN-05 vs RUN-06": ("EVAL-07", "EVAL-08"),
        "Week 4 vs Week 5, M1 workflow: RUN-02 vs RUN-03": ("EVAL-01", "EVAL-05"),
        "Week 4 vs Week 5, M2 workflow: RUN-01 vs RUN-04": ("EVAL-02", "EVAL-06"),
    }
    for name, (e1, e2) in pairs.items():
        p1, p2 = data[e1]["p"], data[e2]["p"]
        assert data[e1]["ids"] == data[e2]["ids"] and data[e1]["keys"] == data[e2]["keys"]
        diff = p1 != p2
        rep[name] = dict(differing_pairs=int(diff.sum()), pairs=int(p1.size),
                         cases_affected=int(diff.any(1).sum()),
                         pos_to_neg=int(((p1 == 1) & (p2 == 0)).sum()), neg_to_pos=int(((p1 == 0) & (p2 == 1)).sum()),
                         kappa=r(kappa(p1, p2)),
                         conditions_affected={k: int(diff[:, j].sum()) for j, k in enumerate(data[e1]["keys"]) if diff[:, j].any()})
    out["ct_run_to_run"] = rep

    # ---------------- D-A compatibility check (CT common-batch rescoring)
    h1, c1, r1 = load_workbook_rows(root / CT_M1)
    h2, c2, r2 = load_workbook_rows(root / CT_GS)
    ids1 = [int(x[c1]) for x in r1]
    ids2 = [int(x[c2]) for x in r2]
    txt_same = all(all((a[h1.index(f)] or "") == (b[h2.index(f)] or "") for f in REPORT_FIELDS) for a, b in zip(r1, r2))
    keys_same = condition_keys(root / CT_M1) == condition_keys(root / CT_GS)
    da = dict(caseids_identical_and_same_order=ids1 == ids2, report_text_identical_all_three_fields=bool(txt_same),
              condition_keys_identical_and_same_order=keys_same,
              run03_predictions=dict(records=len(data["EVAL-05"]["ids"]), keys=len(data["EVAL-05"]["keys"])),
              run04_predictions=dict(records=len(data["EVAL-06"]["ids"]), keys=len(data["EVAL-06"]["keys"])))
    da["compatible"] = bool(da["caseids_identical_and_same_order"] and txt_same and keys_same)
    if da["compatible"]:
        res = {}
        for name, (pe, re_) in {"RUN-03 predictions scored against M2 (Gold Standard)": ("EVAL-05", "EVAL-06"),
                                "RUN-04 predictions scored against M1 (Vetology)": ("EVAL-06", "EVAL-05")}.items():
            y, p = data[re_]["y"], data[pe]["p"]
            tp, fn, tn, fp = [int(c.sum()) for c in counts(y, p)]
            rt = rates(tp, fn, tn, fp)
            res[name] = dict(TP=tp, FN=fn, TN=tn, FP=fp, **{m: r(float(v)) for m, v in rt.items()})
        da["exploratory_rescoring_both_week5_batches"] = res
        # paired M2-minus-M1 contrast on RUN-03 predictions
        y1, y2, p = data["EVAL-05"]["y"], data["EVAL-06"]["y"], data["EVAL-05"]["p"]
        a_ = rates(*[c.sum(1) for c in counts(y1[idx], p[idx])])
        b_ = rates(*[c.sum(1) for c in counts(y2[idx], p[idx])])
        ap_ = rates(*[c.sum() for c in counts(y1, p)])
        bp_ = rates(*[c.sum() for c in counts(y2, p)])
        da["paired_reference_contrast_RUN-03"] = {
            m: dict(point=r(float(bp_[m] - ap_[m])), ci95=[r(v) for v in pct_interval(b_[m] - a_[m])[0]])
            for m in ("accuracy", "sensitivity", "specificity", "precision", "f1")}
    out["d_a_compatibility"] = da

    Path(a.out_json).write_text(json.dumps(out, indent=1), encoding="utf-8")
    Path(a.out_md).write_text(render_md(out), encoding="utf-8")
    print("ok", a.out_json, a.out_md)


# --------------------------------------------------------------------- report
def P(x):
    return "undef." if x is None else f"{100 * x:.2f}%"


def CI(c):
    return "—" if not c else f"{100 * c[0]:.2f}–{100 * c[1]:.2f}%"


def K(x):
    return "undef." if x is None else f"{x:.3f}"


def render_md(o):
    m = o["meta"]
    L = ["# 07 — Statistical Analysis Results (Week 8)", "",
         f"Generated {m['generated_utc']} by `{m['script']}` (seed {m['seed']}, B = {m['bootstrap_replicates']:,}).",
         "Plan: `../03_Consolidated_Knowledge_Base/08_Research_Design_and_Analysis_Plan.md` §6. Deviations: see plan §13.",
         "",
         "**Inputs:** owner-supplied, confidential case-level files (not committed). SHA-256 values are listed at the end. Only aggregate statistics are reported here.",
         "",
         "**Methods recap:**",
         f"- Report-level cluster bootstrap: {m['resampling_unit']}.",
         f"- Intervals: {m['interval']}.",
         f"- Per-condition intervals: {m['wilson']}.",
         f"- F1 = {m['f1_definition']}.",
         "- The same resample indices are used for all evaluations, so paired contrasts on identical cases are paired.",
         "",
         "**Interpretation:** the cases are the first 100 populated records per dataset, not a random sample. Intervals describe variability conditional on these cases, labels, prompts and runs, and imply no population representativeness or clinical validity. They do not include reference-label uncertainty, run-to-run model variation or model drift.",
         "",
         "**Verification:** every evaluation's micro TP/FN/TN/FP was recomputed from predictions plus references and equals the registered counts. The script aborts otherwise.", ""]
    L += ["## 1. Micro (pooled) metrics with 95% report-level bootstrap intervals", "",
          "| Eval | Run | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |",
          "|---|---|---:|---:|---:|---:|---|---|---|---|---|"]
    for eid, e in o["evaluations"].items():
        c = e["counts"]
        cells = [f"{P(e['micro'][k]['point'])} ({CI(e['micro'][k]['ci95'])})" for k in ("accuracy", "sensitivity", "specificity", "precision", "f1")]
        L.append(f"| {eid} {e['label']} | {e['run']} | {c['TP']} | {c['FN']} | {c['TN']} | {c['FP']} | " + " | ".join(cells) + " |")
    und = ", ".join(f"{eid} {k} {v['undefined_replicates']}" for eid, e in o["evaluations"].items()
                    for k, v in e["micro"].items() if v["undefined_replicates"])
    L += ["", "Undefined micro replicates: " + (und or "none in any evaluation or metric."), ""]
    L += ["## 2. Macro averages (defined conditions only) with bootstrap intervals", "",
          "The macro value is the mean of the **defined** condition values. The included/excluded counts refer to the point estimate. In bootstrap replicates the contributing set varies (min–median–max shown), so these intervals are conditional on definedness and approximate.",
          "",
          "| Eval | Metric | Macro | Included / excluded | 95% CI | Contributing conditions in replicates (min / median / max) |",
          "|---|---|---|---|---|---|"]
    for eid, e in o["evaluations"].items():
        for k, v in e["macro"].items():
            cc = v["contributing_conditions_in_replicates"]
            L.append(f"| {eid} | {k} | {P(v['point'])} | {v['included']} / {v['excluded_undefined']} | {CI(v['ci95'])} | {cc['min']} / {cc['median']:.0f} / {cc['max']} |")
    L += ["", "Macro F1 here uses the plan definition (2TP/(2TP+FP+FN)), so it can differ from the workbook macro F1, which excluded conditions where P or S was undefined. The workbook values remain the historical record.", ""]
    L += ["## 3. Paired reference-workflow contrasts (identical predictions)", "",
          "Matrix 2 minus Matrix 1, same prediction set, same resampled reports. This is the controlled reference-effect design (plan §5.2).", "",
          "| Contrast | Accuracy | Sensitivity | Specificity | Precision | F1 |", "|---|---|---|---|---|---|"]

    def D(v):
        return f"{100 * v['point']:+.2f} pp ({100 * v['ci95'][0]:+.2f} to {100 * v['ci95'][1]:+.2f})"
    for name, v in o["paired_reference_contrasts"].items():
        L.append(f"| {name} | " + " | ".join(D(v[k]) for k in ("accuracy", "sensitivity", "specificity", "precision", "f1")) + " |")
    L += ["", "## 4. Agreement between the two reference-label sets (Matrix 1 vs Matrix 2, same cases)", "",
          "| Dataset | Pairs | Raw agreement | Cohen's κ (95% CI, 2,000 report-level resamples) | M1 Pos / M2 Neg | M1 Neg / M2 Pos |",
          "|---|---:|---|---|---:|---:|"]
    for ds, v in o["reference_label_agreement"].items():
        if isinstance(v, str):
            L.append(f"| {ds} | — | {v} | | | |")
            continue
        L.append(f"| {ds} | {v['pairs']:,} | {P(v['agreement'])} | {K(v['kappa'])} ({K(v['kappa_ci95_cluster_bootstrap_2000'][0])}–{K(v['kappa_ci95_cluster_bootstrap_2000'][1])}) | {v['m1_pos_m2_neg']} | {v['m1_neg_m2_pos']} |")
    L += ["", "Per-condition reference agreement is in the JSON file (`reference_label_agreement.*.per_condition`).", ""]
    L += ["## 5. Canine Thorax model comparison (Week 5 gpt-4.1-mini vs Week 7 gemini-3.8-flash) — CT only", "",
          "Agreement is model–model concordance, **not accuracy**. McNemar tests use exact binomial tests of discordant **correctness** per condition across 100 cases, with Holm adjustment within each matrix; they are exploratory. Single run per model, and the confounders in plan §5.2 apply.", ""]
    for mx, v in o["ct_model_comparison"].items():
        L += [f"### {mx} ({v['openai']} vs {v['gemini']})", "",
              f"- Prediction agreement: {v['agreement_pairs']:,}/{v['pairs']:,} ({P(v['agreement_pairs'] / v['pairs'])}); Cohen's κ {K(v['kappa'])} (95% CI {K(v['kappa_ci95_cluster_bootstrap_2000'][0])}–{K(v['kappa_ci95_cluster_bootstrap_2000'][1])}).",
              f"- Testable conditions (≥1 discordant correctness pair): {v['testable_conditions']} of {len(v['per_condition'])}.",
              "- Paired differences (Gemini − OpenAI): " + "; ".join(f"{k} {D(x)}" for k, x in v["paired_difference_gemini_minus_openai"].items()) + ".",
              "", "| Condition | OpenAI-only correct | Gemini-only correct | Exact McNemar p | Holm p | Agreement | κ |", "|---|---:|---:|---|---|---|---|"]
        for c in v["per_condition"]:
            mp = "not testable" if c["mcnemar_exact_p"] is None else f"{c['mcnemar_exact_p']:.4f}"
            hp = "—" if c["holm_p"] is None else f"{c['holm_p']:.4f}"
            L.append(f"| {c['condition']} | {c['openai_only_correct']} | {c['gemini_only_correct']} | {mp} | {hp} | {P(c['agreement'])} | {K(c['kappa'])} |")
        L.append("")
    L += ["## 6. Canine Thorax run-to-run consistency (temperature 0; separate executions on identical report text)", "",
          "| Comparison | Differing pairs | Cases affected | Pos→Neg | Neg→Pos | κ |", "|---|---:|---:|---:|---:|---|"]
    for name, v in o["ct_run_to_run"].items():
        L.append(f"| {name} | {v['differing_pairs']} / {v['pairs']:,} | {v['cases_affected']} | {v['pos_to_neg']} | {v['neg_to_pos']} | {K(v['kappa'])} |")
    L += ["", "The Week 4 vs Week 5 rows compare different application versions on the same workflow inputs (a quasi-repeat, plan §5.2). Conditions affected are in the JSON file.", ""]
    da = o["d_a_compatibility"]
    L += ["## 7. Decision D-A — compatibility check for CT common-batch rescoring", "",
          f"- CaseIDs identical and in the same order in the M1 and M2 workbooks: **{da['caseids_identical_and_same_order']}**",
          f"- Report text identical (Findings, Conclusions, Recommendations), all 100 cases: **{da['report_text_identical_all_three_fields']}**",
          f"- Condition keys identical and in the same order: **{da['condition_keys_identical_and_same_order']}**",
          f"- RUN-03: {da['run03_predictions']['records']} success records × {da['run03_predictions']['keys']} keys; RUN-04: {da['run04_predictions']['records']} × {da['run04_predictions']['keys']}",
          f"- **Compatible: {da['compatible']}**", ""]
    if da.get("exploratory_rescoring_both_week5_batches"):
        L += ["**Exploratory rescoring of both Week 5 batches.** This is not a selection: D-A remains an owner decision. These are new, additional analyses, and they do not replace EVAL-05 or EVAL-06.", "",
              "| Rescoring | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |", "|---|---:|---:|---:|---:|---|---|---|---|---|"]
        for name, v in da["exploratory_rescoring_both_week5_batches"].items():
            L.append(f"| {name} | {v['TP']} | {v['FN']} | {v['TN']} | {v['FP']} | {P(v['accuracy'])} | {P(v['sensitivity'])} | {P(v['specificity'])} | {P(v['precision'])} | {P(v['f1'])} |")
        L += ["", "Paired M2 − M1 contrast on RUN-03 predictions (same prediction set; analogous to the FT/CA design): " +
              "; ".join(f"{k} {D(v)}" for k, v in da["paired_reference_contrast_RUN-03"].items()) + ".", ""]
    L += ["## 8. Per-condition results with 95% Wilson intervals", "",
          "Sens = TP/(TP+FN); Spec = TN/(TN+FP); Prec = TP/(TP+FP). \"undef.\" = zero denominator. Bootstrap-undefined counts (out of B) show how often a metric was undefined in resamples.", ""]
    for eid, e in o["evaluations"].items():
        L += [f"### {eid} — {e['label']}", "", "| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |",
              "|---|---|---:|---|---|---|---|---|"]
        for c in e["conditions"]:
            u = c["bootstrap_undefined_replicates"]
            L.append(f"| {c['condition']} | {c['ref_pos']} / {c['ref_neg']} | {c['pred_pos']} | {P(c['sensitivity']['point'])} ({CI(c['sensitivity']['wilson95'])}) | {P(c['specificity']['point'])} ({CI(c['specificity']['wilson95'])}) | {P(c['precision']['point'])} ({CI(c['precision']['wilson95'])}) | {P(c['f1'])} | {u['sensitivity']} / {u['precision']} / {u['f1']} |")
        L.append("")
    L += ["## 9. Input file hashes (SHA-256)", "", "| File (relative to bundle root) | SHA-256 |", "|---|---|"]
    for f, h in m["inputs"].items():
        L.append(f"| `{f}` | `{h}` |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
