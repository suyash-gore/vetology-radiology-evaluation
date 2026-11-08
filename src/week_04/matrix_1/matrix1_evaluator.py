"""Build the independent Matrix 1 evaluation workbook."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter

CONDITIONS = [
    "perihilar_infiltrate", "pneumonia", "bronchitis", "interstitial",
    "diseased_lungs", "hypo_plastic_trachea", "cardiomegaly",
    "pulmonary_nodules", "pleural_effusion", "rtm",
    "focal_caudodorsal_lung", "focal_perihilar", "pulmonary_hypoinflation",
    "right_sided_cardiomegaly", "pericardial_effusion", "bronchiectasis",
    "pulmonary_vessel_enlargement", "left_sided_cardiomegaly",
    "thoracic_lymphadenopathy", "esophagitis",
]

def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None

def load_matrix1_inputs(ground_truth_path, predictions_path):
    workbook = load_workbook(ground_truth_path, data_only=True, read_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    headers = [cell.value for cell in sheet[1]]
    required = ["CaseID", *CONDITIONS]
    missing = [name for name in required if name not in headers]
    if missing:
        raise ValueError(f"Missing ground-truth columns: {missing}")
    positions = {name: headers.index(name) for name in required}
    ground_truth = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[positions["CaseID"]] is None:
            continue
        case_id = int(row[positions["CaseID"]])
        if case_id in ground_truth:
            raise ValueError(f"Duplicate ground-truth CaseID: {case_id}")
        ground_truth[case_id] = {}
        for condition in CONDITIONS:
            label = row[positions[condition]]
            if label not in ("Positive", "Negative"):
                raise ValueError(f"Invalid ground-truth label: CaseID={case_id}, {condition}={label}")
            ground_truth[case_id][condition] = label
    workbook.close()

    predictions = {}
    with open(predictions_path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            case_id = int(record["case_id"])
            if case_id in predictions:
                raise ValueError(f"Duplicate prediction CaseID: {case_id}")
            if record.get("status") != "success":
                raise ValueError(f"Prediction is not successful for CaseID {case_id}")
            labels = record.get("predictions", {})
            if set(labels) != set(CONDITIONS):
                raise ValueError(f"Prediction keys mismatch for CaseID {case_id}")
            if any(value not in ("Positive", "Negative") for value in labels.values()):
                raise ValueError(f"Invalid prediction label for CaseID {case_id}")
            predictions[case_id] = labels
    if set(ground_truth) != set(predictions):
        raise ValueError(
            "CaseID mismatch: "
            f"ground-truth-only={sorted(set(ground_truth)-set(predictions))}; "
            f"prediction-only={sorted(set(predictions)-set(ground_truth))}"
        )
    if len(ground_truth) != 100:
        raise ValueError(f"Matrix 1 requires exactly 100 cases; found {len(ground_truth)}")
    return ground_truth, predictions

def calculate_condition_metrics(ground_truth, predictions):
    results = {}
    for condition in CONDITIONS:
        tp = fn = tn = fp = 0
        for case_id in ground_truth:
            actual = ground_truth[case_id][condition]
            predicted = predictions[case_id][condition]
            if actual == "Positive" and predicted == "Positive": tp += 1
            elif actual == "Positive" and predicted == "Negative": fn += 1
            elif actual == "Negative" and predicted == "Negative": tn += 1
            else: fp += 1
        precision = _ratio(tp, tp + fp)
        sensitivity = _ratio(tp, tp + fn)
        specificity = _ratio(tn, tn + fp)
        f1 = None
        if precision is not None and sensitivity is not None and precision + sensitivity:
            f1 = 2 * precision * sensitivity / (precision + sensitivity)
        total = tp + fn + tn + fp
        results[condition] = {
            "tp": tp, "fn": fn, "tn": tn, "fp": fp, "total": total,
            "positive_gt": tp + fn, "negative_gt": tn + fp,
            "accuracy": _ratio(tp + tn, total), "sensitivity": sensitivity,
            "specificity": specificity, "precision": precision, "f1": f1,
        }
    return results

def _mean_defined(values):
    defined = [value for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None

def build_evaluation_workbook(ground_truth, predictions, output_path, ground_truth_path=None, predictions_path=None):
    metrics = calculate_condition_metrics(ground_truth, predictions)
    totals = {key: sum(metrics[c][key] for c in CONDITIONS)
              for key in ("tp", "fn", "tn", "fp", "total", "positive_gt", "negative_gt")}
    totals.update({
        "accuracy": _ratio(totals["tp"] + totals["tn"], totals["total"]),
        "sensitivity": _ratio(totals["tp"], totals["tp"] + totals["fn"]),
        "specificity": _ratio(totals["tn"], totals["tn"] + totals["fp"]),
        "precision": _ratio(totals["tp"], totals["tp"] + totals["fp"]),
    })
    totals["f1"] = None
    if totals["precision"] is not None and totals["sensitivity"] is not None and totals["precision"] + totals["sensitivity"]:
        totals["f1"] = 2 * totals["precision"] * totals["sensitivity"] / (totals["precision"] + totals["sensitivity"])

    wb = Workbook()
    summary = wb.active
    summary.title = "Overall Summary"
    summary.append(["VETOLOGY MATRIX 1 - EVALUATION SUMMARY"])
    summary.append(["Metric", "Result", "Calculation / Definition", "Interpretation"])
    summary_rows = [
        ("Cases evaluated", len(ground_truth), "Unique matched CaseIDs", "Fresh 100-case Matrix 1 evaluation."),
        ("Conditions evaluated", len(CONDITIONS), "Condition columns", "All 20 Matrix 1 conditions evaluated independently."),
        ("Total paired labels", totals["total"], "Cases × conditions", "Each case-condition pair contributes one comparison."),
        ("True Positive (TP)", totals["tp"], "GS Positive; model Positive", "Correctly identified positive labels."),
        ("False Negative (FN)", totals["fn"], "GS Positive; model Negative", "Positive labels missed by the model."),
        ("True Negative (TN)", totals["tn"], "GS Negative; model Negative", "Correctly identified negative labels."),
        ("False Positive (FP)", totals["fp"], "GS Negative; model Positive", "Negative labels incorrectly predicted positive."),
        ("Micro Accuracy", totals["accuracy"], "(TP + TN) / all paired labels", "Overall agreement across all case-condition pairs."),
        ("Micro Sensitivity (Recall)", totals["sensitivity"], "TP / (TP + FN)", "Recall across all Gold Standard Positive labels."),
        ("Micro Specificity", totals["specificity"], "TN / (TN + FP)", "Correct rejection rate across all Gold Standard Negative labels."),
        ("Micro Precision", totals["precision"], "TP / (TP + FP)", "Proportion of model-positive labels that are Gold Standard Positive."),
        ("Micro F1-score", totals["f1"], "2 × Precision × Sensitivity / (Precision + Sensitivity)", "Harmonic mean of micro precision and sensitivity."),
        ("Macro Accuracy", _mean_defined([metrics[c]["accuracy"] for c in CONDITIONS]), "Mean of condition-level accuracies", "Each condition receives equal weight."),
        ("Macro Sensitivity", _mean_defined([metrics[c]["sensitivity"] for c in CONDITIONS]), "Mean of defined condition-level sensitivities", "Undefined conditions are excluded, not set to zero."),
        ("Macro Specificity", _mean_defined([metrics[c]["specificity"] for c in CONDITIONS]), "Mean of defined condition-level specificities", "Undefined conditions are excluded, not set to zero."),
        ("Macro Precision", _mean_defined([metrics[c]["precision"] for c in CONDITIONS]), "Mean of defined condition-level precisions", "Undefined conditions are excluded, not set to zero."),
        ("Macro F1-score", _mean_defined([metrics[c]["f1"] for c in CONDITIONS]), "Mean of defined condition-level F1-scores", "Undefined conditions are excluded, not set to zero."),
    ]
    for row in summary_rows: summary.append(list(row))

    condition_sheet = wb.create_sheet("Condition Summary")
    condition_sheet.append(["Condition","TP","FN","TN","FP","Total","Positive Ground Truth","Negative Ground Truth","Accuracy","Sensitivity","Specificity","Precision","F1-score"])
    for condition in CONDITIONS:
        m = metrics[condition]
        condition_sheet.append([condition,m["tp"],m["fn"],m["tn"],m["fp"],m["total"],m["positive_gt"],m["negative_gt"],m["accuracy"],m["sensitivity"],m["specificity"],m["precision"],m["f1"]])
    condition_sheet.append(["TOTAL",totals["tp"],totals["fn"],totals["tn"],totals["fp"],totals["total"],totals["positive_gt"],totals["negative_gt"],totals["accuracy"],totals["sensitivity"],totals["specificity"],totals["precision"],totals["f1"]])

    case_sheet = wb.create_sheet("Case Predictions")
    columns = ["CaseID"]
    for condition in CONDITIONS:
        columns.extend([f"{condition} - Gold Standard", f"{condition} - Model Prediction", f"{condition} - Agreement"])
    case_sheet.append(columns)
    for case_id in sorted(ground_truth):
        row = [case_id]
        for condition in CONDITIONS:
            actual, predicted = ground_truth[case_id][condition], predictions[case_id][condition]
            row.extend([actual, predicted, "Match" if actual == predicted else "Mismatch"])
        case_sheet.append(row)

    confusion = wb.create_sheet("Confusion Matrix")
    confusion.append(["Condition","True Positive","False Negative","True Negative","False Positive","Sensitivity","Specificity","Check","Positive Ground Truth","Negative Ground Truth","Accuracy","Precision","F1-score","Total"])
    for condition in CONDITIONS:
        m = metrics[condition]
        confusion.append([condition,m["tp"],m["fn"],m["tn"],m["fp"],m["sensitivity"],m["specificity"],m["total"],m["positive_gt"],m["negative_gt"],m["accuracy"],m["precision"],m["f1"],m["total"]])
    confusion.append(["TOTAL",totals["tp"],totals["fn"],totals["tn"],totals["fp"],totals["sensitivity"],totals["specificity"],totals["total"],totals["positive_gt"],totals["negative_gt"],totals["accuracy"],totals["precision"],totals["f1"],totals["total"]])

    log = wb.create_sheet("Execution Log")
    log.append(["Metric","Value"])
    for row in [
        ("Evaluation Track","Matrix 1 only — kept separate from Matrix 2"),
        ("Ground-truth workbook",Path(ground_truth_path).name if ground_truth_path else "Matrix 1 encoded ground-truth workbook"),
        ("Prediction file",Path(predictions_path).name if predictions_path else "Matrix 1 predictions.jsonl"),
        ("Cases in ground truth",len(ground_truth)),
        ("Prediction records",len(predictions)),
        ("Conditions",len(CONDITIONS)),
        ("Expected paired labels",len(ground_truth)*len(CONDITIONS)),
        ("Actual paired labels",totals["total"]),
        ("CaseID reconciliation","PASS — exact match; no missing, duplicate, or unexpected CaseIDs"),
        ("Prediction validation","PASS — all records successful; exact 20 keys; Positive/Negative labels only"),
        ("Model","gpt-4.1-mini (Matrix 1 batch execution record)"),
        ("Prompt version","Canine Thorax Master Prompt V1.3"),
        ("Evaluation generated (UTC)",datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Metric scope","Matrix 1 encoded ground truth compared with Matrix 1 predictions only"),
        ("Clinical interpretation","Dataset-specific evaluation; not a statement of clinical readiness."),
    ]: log.append(list(row))

    definitions = wb.create_sheet("Metric Definitions")
    definitions.append(["Term","Definition"])
    for row in [
        ("TP","Ground Truth = Positive and Model Prediction = Positive."),
        ("FN","Ground Truth = Positive and Model Prediction = Negative."),
        ("TN","Ground Truth = Negative and Model Prediction = Negative."),
        ("FP","Ground Truth = Negative and Model Prediction = Positive."),
        ("Accuracy","(TP + TN) / (TP + FN + TN + FP)."),
        ("Sensitivity / Recall","TP / (TP + FN). Undefined when there are no Gold Standard Positive labels."),
        ("Specificity","TN / (TN + FP). Undefined when there are no Gold Standard Negative labels."),
        ("Precision","TP / (TP + FP). Undefined when the model makes no Positive predictions."),
        ("F1-score","2 × Precision × Sensitivity / (Precision + Sensitivity). Undefined if either component is undefined or their sum is zero."),
        ("Micro average","Metrics calculated after summing TP, FN, TN, and FP across all conditions."),
        ("Macro average","Unweighted mean of defined condition-level values. Undefined values are excluded, not treated as zero."),
        ("Separation rule","Matrix 1 results are not combined with Matrix 2 results."),
    ]: definitions.append(list(row))

    navy, pale_blue, pale_green, pale_red = "1F4E78", "D9EAF7", "E2F0D9", "FCE4D6"
    thin = Side(style="thin", color="D9E1F2")
    for sheet in wb.worksheets:
        sheet.freeze_panes = "B3" if sheet.title == "Overall Summary" else "B2"
        if sheet.title in ("Condition Summary","Case Predictions","Confusion Matrix"):
            sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.fill = PatternFill("solid", fgColor=navy)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        sheet.row_dimensions[1].height = 30
        if sheet.title == "Overall Summary":
            for cell in sheet[2]:
                cell.fill = PatternFill("solid", fgColor=pale_blue); cell.font = Font(bold=True)
            for row in range(3, sheet.max_row+1):
                if row in range(10,20): sheet.cell(row,2).number_format = "0.00%"
            widths = [30,18,58,65]
        elif sheet.title == "Condition Summary":
            for row in range(2,sheet.max_row+1):
                for col in range(9,14): sheet.cell(row,col).number_format = "0.00%"
            for cell in sheet[sheet.max_row]:
                cell.fill = PatternFill("solid", fgColor=pale_green); cell.font = Font(bold=True)
            widths = [30,10,10,10,10,10,20,20,13,13,13,13,13]
        elif sheet.title == "Confusion Matrix":
            for row in range(2,sheet.max_row+1):
                for col in (6,7,11,12,13): sheet.cell(row,col).number_format = "0.00%"
            for cell in sheet[sheet.max_row]:
                cell.fill = PatternFill("solid", fgColor=pale_green); cell.font = Font(bold=True)
            widths = [30,15,15,15,15,14,14,12,20,20,14,14,14,12]
        elif sheet.title == "Case Predictions":
            widths = [12] + [22,22,14] * len(CONDITIONS)
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    if cell.value == "Mismatch": cell.fill = PatternFill("solid", fgColor=pale_red)
                    elif cell.value == "Match": cell.fill = PatternFill("solid", fgColor=pale_green)
        elif sheet.title == "Execution Log": widths = [32,90]
        else: widths = [32,100]
        for index, width in enumerate(widths,1):
            sheet.column_dimensions[get_column_letter(index)].width = width
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                cell.border = Border(bottom=thin)
    wb.save(output_path)
    return metrics, totals

def main():
    parser = argparse.ArgumentParser(description="Generate Matrix 1 evaluation workbook.")
    parser.add_argument("--ground-truth", required=True, help="Path to Matrix 1 encoded ground-truth .xlsx")
    parser.add_argument("--predictions", required=True, help="Path to Matrix 1 predictions.jsonl")
    parser.add_argument("--output", default="outputs/week_04/matrix_1/matrix1_evaluation_workbook.xlsx")
    args = parser.parse_args()
    ground_truth, predictions = load_matrix1_inputs(args.ground_truth, args.predictions)
    metrics, totals = build_evaluation_workbook(ground_truth, predictions, args.output, args.ground_truth, args.predictions)
    print(f"Matrix 1 evaluation workbook created: {args.output}")
    print(f"Cases: {len(ground_truth)} | Conditions: {len(CONDITIONS)} | Paired labels: {totals['total']}")
    print(f"TP={totals['tp']} FN={totals['fn']} TN={totals['tn']} FP={totals['fp']}")
    print(f"Micro accuracy={totals['accuracy']:.4%} | sensitivity={totals['sensitivity']:.4%} | specificity={totals['specificity']:.4%}")
if __name__ == "__main__":
    main()
