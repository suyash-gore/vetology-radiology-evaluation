"""Six-sheet comparison workbook: structure, values, separation, provenance and isolation."""
from __future__ import annotations

import contextlib
import io
import os
import tempfile
from pathlib import Path
from unittest import mock

from openpyxl import load_workbook

from week_07 import cli, config
from week_07.comparison.compare import compare_workflow
from week_07.comparison.comparison_workbook import (
    AGREEMENT_HEADERS,
    CONDITION_HEADERS,
    DISAGREEMENT_HEADERS,
    NO_DISAGREEMENTS,
    SHEETS,
    build_comparison_workbook,
    display_path,
    write_comparison_workbook,
)
from week_07.comparison.sources import OPENAI_MODEL_RECORD, ComparisonInputError
from week_07.conditions import CONDITION_KEYS
from week_07.evaluation.workbook_compare import compare_workbooks
from week_07.isolation import IsolationError, ProtectedFileModified, sha256_file
from week_07.tests.fixtures import (
    GEMINI_FLIPS,
    SyntheticRepo,
    run_week7_gemini,
    write_week5_openai,
)
from week_07.tests.gemini_fakes import StepClock
from week_07.tests.support import OfflineTestCase, quiet

VARIANT = {"matrix1": 0, "matrix2": 1}


class WorkbookTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()

    def result(self, name, **openai_kwargs):
        write_week5_openai(self.repo, name, VARIANT[name], **openai_kwargs)
        run_week7_gemini(self.repo, name, VARIANT[name])
        return compare_workflow(self.repo.spec(name), isolation=self.repo.policy)

    def book(self, name, **openai_kwargs):
        result = self.result(name, **openai_kwargs)
        path = write_comparison_workbook(self.repo.spec(name), result,
                                         isolation=self.repo.policy, clock=StepClock())
        return result, path, load_workbook(path)


def column(ws, header_row, header):
    headers = [c.value for c in ws[header_row]]
    return headers.index(header) + 1


class TestStructure(WorkbookTestCase):
    def test_six_sheets_in_order_and_default_location(self):
        for name, filename in (("matrix1", "matrix1_openai_vs_gemini_comparison.xlsx"),
                               ("matrix2", "matrix2_openai_vs_gemini_comparison.xlsx")):
            with self.subTest(workflow=name):
                _, path, book = self.book(name)
                self.assertEqual(path, self.repo.spec(name).comparison_dir / filename)
                self.assertEqual(tuple(book.sheetnames), SHEETS)
                self.assertEqual(SHEETS, ("Overall Comparison", "Condition Comparison",
                                          "Model Agreement", "Case Disagreements",
                                          "Execution Log", "Metric Definitions"))

    def test_headers_and_row_counts(self):
        result, _, book = self.book("matrix2")
        cond, agree, dis = (book["Condition Comparison"], book["Model Agreement"],
                            book["Case Disagreements"])
        self.assertEqual([c.value for c in cond[1]], CONDITION_HEADERS)
        self.assertEqual([c.value for c in agree[1]], AGREEMENT_HEADERS)
        self.assertEqual([c.value for c in dis[1]], DISAGREEMENT_HEADERS)
        self.assertEqual([cond.cell(r, 1).value for r in range(2, 22)], list(CONDITION_KEYS))
        self.assertEqual((cond.max_row, cond.cell(22, 1).value), (22, "MICRO TOTAL"))
        self.assertEqual((agree.max_row, agree.cell(22, 1).value), (22, "TOTAL"))
        self.assertEqual(dis.max_row, 1 + len(result.disagreements))
        overall = book["Overall Comparison"]
        self.assertEqual([c.value for c in overall[3]],
                         ["Metric", "Week 5 OpenAI", "Week 7 Gemini",
                          "Difference (Gemini − OpenAI)", "Definition"])
        self.assertIn("MATRIX 2 MODEL COMPARISON", overall["A1"].value)
        self.assertIn("Gold Standard", overall["A2"].value)

    def test_macro_rows_only_for_matrix1(self):
        _, _, m1 = self.book("matrix1")
        _, _, m2 = self.book("matrix2")
        rows = lambda ws: [ws.cell(r, 1).value for r in range(4, ws.max_row + 1)]  # noqa: E731
        self.assertIn("Macro F1-score", rows(m1["Overall Comparison"]))
        self.assertNotIn("Macro F1-score", rows(m2["Overall Comparison"]))
        self.assertIn("Vetology", m1["Overall Comparison"]["A2"].value)

    def test_percent_formats(self):
        _, _, book = self.book("matrix1")
        cond = book["Condition Comparison"]
        for header in ("Week 5 OpenAI Accuracy", "Week 7 Gemini F1-score",
                       "Difference Sensitivity"):
            self.assertEqual(cond.cell(2, column(cond, 1, header)).number_format, "0.00%")
        self.assertEqual(cond.cell(2, column(cond, 1, "Week 5 OpenAI TP")).number_format,
                         "General")
        agree = book["Model Agreement"]
        self.assertEqual(agree.cell(2, column(agree, 1, "Agreement Rate")).number_format,
                         "0.00%")


class TestValues(WorkbookTestCase):
    def test_overall_values_match_result(self):
        result, _, book = self.book("matrix1")
        ws = book["Overall Comparison"]
        rows = {ws.cell(r, 1).value: [ws.cell(r, c).value for c in (2, 3, 4)]
                for r in range(4, ws.max_row + 1)}
        o, g = result.openai_evaluation, result.gemini_evaluation
        self.assertEqual(rows["True Positive (TP)"], [o.micro.tp, g.micro.tp,
                                                      g.micro.tp - o.micro.tp])
        self.assertAlmostEqual(rows["Micro Accuracy"][2], g.micro.accuracy - o.micro.accuracy)
        self.assertEqual(rows["Macro Accuracy"][:2], [o.macro.accuracy, g.macro.accuracy])
        c = result.correctness_total
        self.assertEqual(rows["Only Gemini correct"][0], c.only_gemini_correct)
        self.assertEqual(rows["Both models wrong"][0], c.both_wrong)

    def test_model_agreement_sheet_matches_result(self):
        result, _, book = self.book("matrix2")
        ws = book["Model Agreement"]
        total = [ws.cell(22, c).value for c in range(1, 12)]
        a = result.agreement_total
        self.assertEqual(total, ["TOTAL", a.both_positive, a.openai_only_positive,
                                 a.gemini_only_positive, a.both_negative, a.total, a.agreements,
                                 a.disagreements, a.agreement_rate, a.openai_positive,
                                 a.gemini_positive])
        rtm = [ws.cell(2 + CONDITION_KEYS.index("rtm"), c).value for c in range(2, 6)]
        r = result.agreement["rtm"]
        self.assertEqual(rtm, [r.both_positive, r.openai_only_positive, r.gemini_only_positive,
                               r.both_negative])

    def test_agreement_sheet_contains_no_reference_based_columns(self):
        _, _, book = self.book("matrix2")
        headers = [c.value for c in book["Model Agreement"][1]]
        for word in ("Correct", "Reference", "Accuracy", "Sensitivity", "TP"):
            self.assertFalse(any(word in h for h in headers), word)

    def test_disagreement_rows(self):
        result, _, book = self.book("matrix2")
        ws = book["Case Disagreements"]
        rows = [[ws.cell(r, c).value for c in range(1, 7)] for r in range(2, ws.max_row + 1)]
        self.assertEqual(rows, [[d.case_id, d.condition, d.reference, d.openai, d.gemini,
                                 d.model_matching_reference] for d in result.disagreements])
        self.assertEqual([r[:2] for r in rows], sorted(
            (r[:2] for r in rows), key=lambda x: (x[0], CONDITION_KEYS.index(x[1]))))

    def test_no_disagreements_is_stated(self):
        _, _, book = self.book("matrix2", flips=GEMINI_FLIPS)
        ws = book["Case Disagreements"]
        self.assertEqual((ws.max_row, ws["A2"].value), (2, NO_DISAGREEMENTS))

    def test_undefined_values_are_blank(self):
        self.repo.write_inputs(m2_cases=range(1, 4))
        write_week5_openai(self.repo, "matrix2", 1, case_ids=range(1, 4))
        run_week7_gemini(self.repo, "matrix2", 1)
        result = compare_workflow(self.repo.m2, isolation=self.repo.policy)
        undefined = [c for c in CONDITION_KEYS
                     if result.openai_evaluation.per_condition[c].sensitivity is None]
        self.assertTrue(undefined)
        book = build_comparison_workbook(result, clock=StepClock())
        ws = book["Condition Comparison"]
        row = 2 + CONDITION_KEYS.index(undefined[0])
        for header in ("Week 5 OpenAI Sensitivity", "Week 7 Gemini Sensitivity",
                       "Difference Sensitivity"):
            self.assertIsNone(ws.cell(row, column(ws, 1, header)).value)

    def test_deterministic_with_fixed_clock(self):
        result = self.result("matrix1")
        a = build_comparison_workbook(result, clock=StepClock())
        b = build_comparison_workbook(result, clock=StepClock())
        self.assertEqual(compare_workbooks(a, b), [])


class TestExecutionLog(WorkbookTestCase):
    def log(self, book):
        ws = book["Execution Log"]
        return [[ws.cell(r, c).value for c in (1, 2, 3)] for r in range(2, ws.max_row + 1)]

    def test_provenance_and_digests(self):
        result, _, book = self.book("matrix1", error_case_ids=range(1, 101))
        rows = self.log(book)
        items = {r[0]: r for r in rows}
        spec = self.repo.m1
        self.assertIn("Matrix 1", items["Comparison"][1])
        self.assertIn("never combined", items["Comparison"][2])
        self.assertEqual(items["Reference labels"][1], "Original Vetology condition scores")
        self.assertIn(sha256_file(spec.default_input_path), items["Reference workbook"][2])
        self.assertIn(sha256_file(spec.week5_predictions_path),
                      items["Week 5 OpenAI predictions"][2])
        self.assertIn(sha256_file(spec.predictions_path), items["Week 7 Gemini predictions"][2])
        self.assertIn(sha256_file(spec.manifest_path), items["Week 7 Gemini run manifest"][2])
        self.assertEqual(items["Week 5 OpenAI model"][1], OPENAI_MODEL_RECORD)
        self.assertTrue(items["Week 7 Gemini model"][1].startswith("gemini-3.8-flash"))
        self.assertEqual(items["Week 5 OpenAI superseded failures"][1], 100)
        self.assertIn("1–100", items["Week 5 OpenAI superseded failures"][2])
        self.assertEqual(items["Week 5 OpenAI final failures"][1], 0)
        self.assertEqual(items["Week 7 Gemini final failures"][1], 0)
        self.assertEqual(items["API requests"][1], "None")
        digests = {r[1]: r[2] for r in rows if r[0] == "Source file SHA-256"}
        self.assertEqual(digests, {display_path(p): d for p, d in result.source_digests.items()})
        self.assertEqual(len(digests), 5)  # five distinct files, none collapsed by name
        self.assertIn("week_05/matrix_1/predictions.jsonl", digests)
        self.assertIn("week_07/matrix_1/predictions.jsonl", digests)

    def test_skipped_lines_listed(self):
        _, _, book = self.book("matrix2", extra_lines=['{"case_id": 9, "sta'])
        items = {r[0]: r for r in self.log(book)}
        self.assertEqual(items["Week 5 OpenAI skipped prediction lines"][1], 1)
        self.assertIn("line 101", items["Week 5 OpenAI skipped prediction lines"][2])


class TestWriteIsolation(WorkbookTestCase):
    def test_refused_targets(self):
        result = self.result("matrix1")
        for target in (self.repo.m1.week5_output_dir / "x.xlsx",
                       self.repo.m1.output_dir / "x.xlsx",
                       self.repo.m2.comparison_dir / "x.xlsx",
                       self.repo.root / "data" / "x.xlsx",
                       self.repo.root / "x.xlsx"):
            with self.subTest(target=target), self.assertRaises(IsolationError):
                write_comparison_workbook(self.repo.m1, result, target,
                                          isolation=self.repo.policy)

    def test_result_for_other_workflow_refused(self):
        result = self.result("matrix1")
        with self.assertRaises(ValueError):
            write_comparison_workbook(self.repo.m2, result, isolation=self.repo.policy)


class TestCompareCommand(OfflineTestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (mock.patch.object(config, "ENV_FILE", Path(tmp.name) / "absent.env"),
                        mock.patch.dict(os.environ, {}, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            return cli.main(list(argv)), out.getvalue()

    def test_exit_codes(self):
        for error, code in ((ComparisonInputError("bad"), 3), (FileNotFoundError("x"), 3),
                            (ProtectedFileModified("changed"), 7),
                            (IsolationError("blocked"), 2)):
            with self.subTest(error=type(error).__name__), \
                    mock.patch("week_07.comparison.compare.compare_workflow", side_effect=error):
                self.assertEqual(self.run_cli("compare", "--workflow", "matrix1")[0], code)

    def test_arguments_reach_the_engine_and_summary_is_printed(self):
        repo = SyntheticRepo()
        self.addCleanup(repo.cleanup)
        repo.write_inputs()
        write_week5_openai(repo, "matrix2", 1)
        run_week7_gemini(repo, "matrix2", 1)
        real = compare_workflow(repo.m2, isolation=repo.policy)
        with mock.patch("week_07.comparison.compare.compare_workflow",
                        return_value=real) as engine, \
                mock.patch("week_07.comparison.comparison_workbook.write_comparison_workbook",
                           return_value=Path("synthetic.xlsx")) as writer:
            code, text = self.run_cli("compare", "--workflow", "matrix2", "--openai", "a.jsonl",
                                      "--gemini", "b.jsonl", "--openai-errors", "e.jsonl")
        self.assertEqual(code, 0)
        kwargs = engine.call_args.kwargs
        self.assertEqual((kwargs["openai_path"], kwargs["gemini_path"],
                          kwargs["openai_errors_path"]), ("a.jsonl", "b.jsonl", "e.jsonl"))
        writer.assert_called_once()
        for expected in ("Model agreement (reference not used)", OPENAI_MODEL_RECORD,
                         "No API request was made.", "Read-only source unchanged"):
            self.assertIn(expected, text)

    def test_missing_week5_files_in_cloud_are_input_errors(self):
        code, text = self.run_cli("compare", "--workflow", "matrix1",
                                  "--reference", str(Path(__file__)))
        self.assertEqual(code, 3)
        self.assertIn("not found", text)
