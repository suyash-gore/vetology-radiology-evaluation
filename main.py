
"""Read a radiology Excel file and create a confusion matrix workbook."""

import argparse
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill


# The first eight columns contain case information and radiologist/AI reports.
# Disease condition columns begin after these metadata columns.
METADATA_COLUMN_COUNT = 8

# These headers define the layout of the generated confusion matrix.
# None entries preserve blank spacer columns from the example workbook.
OUTPUT_HEADERS = [
    "condition",
    "True Positive",
    "False Negative",
    "True Negative",
    "False Positive",
    "Sensitivity",
    "Specificity",
    "Check",
    "Positive Ground Truth",
    "Negative Ground Truth",
    "Ground Truth Check",
    None,
    "Radiologist Agreement Rate",
    None,
]


def create_output_workbook(conditions, output_path):
    """Create an Excel workbook matching the example output structure."""
    # Create a new workbook and rename its active worksheet.
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Confusion Matrix"

    # Write the column headers and apply formatting to match the example.
    for column, header in enumerate(OUTPUT_HEADERS, start=1):
        cell = sheet.cell(row=1, column=column, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="2EA3F2",
        )
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    # Add one row for each disease condition detected in the input workbook.
    for row_number, condition in enumerate(conditions, start=2):
        sheet.cell(row=row_number, column=1, value=condition)

        # The confusion-matrix counts are not calculated at this stage.
        # Counts are not calculated at this stage.
        # Sensitivity = True Positive / (True Positive + False Negative).
        sheet.cell(
            row=row_number,
            column=6,
            value=(
                f'=IFERROR(B{row_number}/'
                f'(B{row_number}+C{row_number}),0)'
            ),
        )

        # Specificity = True Negative / (True Negative + False Positive).
        # IFERROR returns zero if the calculation produces an error.
        sheet.cell(
            row=row_number,
            column=7,
            value=(
                f'=IFERROR(D{row_number}/'
                f'(D{row_number}+E{row_number}),0)'
            ),
        )

        # Calculate a total from the four confusion-matrix count cells.
        sheet.cell(
            row=row_number,
            column=8,
            value=f'=SUM(B{row_number}:E{row_number})',
        )

        # Calculate the positive ground-truth total from TP and FN.
        sheet.cell(
            row=row_number,
            column=9,
            value=f'=SUM(B{row_number}:C{row_number})',
        )

        # Calculate the negative ground-truth total from TN and FP.
        sheet.cell(
            row=row_number,
            column=10,
            value=f'=SUM(D{row_number}:E{row_number})',
        )

        # Compare the combined positive and negative ground-truth totals.
        sheet.cell(
            row=row_number,
            column=11,
            value=f'=SUM(I{row_number}:J{row_number})',
        )

    # Keep the header visible while scrolling through the condition rows.
    sheet.freeze_panes = "B2"

    # Enable filtering across the headers and all generated condition rows.
    sheet.auto_filter.ref = f"A1:N{max(1, len(conditions) + 1)}"

    # Set column widths to make headers and condition names easier to read.
    sheet.column_dimensions["A"].width = 30
    for column in "BCDEFGHIJKLMN":
        sheet.column_dimensions[column].width = 18

    # Increase the header height to accommodate wrapped text.
    sheet.row_dimensions[1].height = 35

    # Create the output directory if it does not already exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the generated workbook to the requested output path.
    workbook.save(output_path)


def main():
    """Parse arguments, read input Excel, and create output Excel."""
    # Configure the command-line interface and its help description.
    parser = argparse.ArgumentParser(
        description="Prepare a confusion matrix output workbook."
    )

    # Require the user to supply the input Excel file path.
    parser.add_argument(
        "input_file",
        help="Path to the input Excel file.",
    )

    # Allow an optional output path; otherwise, use the default filename.
    parser.add_argument(
        "-o",
        "--output",
        help="Output workbook path.",
    )

    # Parse the arguments supplied in the terminal.
    args = parser.parse_args()
    input_path = Path(args.input_file)

    # Stop if the supplied input path does not point to an existing file.
    if not input_path.is_file():
        parser.error(f"Input file does not exist: {input_path}")

    # Accept only the supported Excel workbook extensions.
    if input_path.suffix.lower() not in {".xlsx", ".xlsm"}:
        parser.error("Input must be an .xlsx or .xlsm file.")

    try:
        # Open the workbook in read-only mode to avoid modifying the source.
        # data_only=True reads cached formula results where available.
        source_workbook = openpyxl.load_workbook(
            input_path,
            read_only=True,
            data_only=True,
        )

        try:
            # Report file and workbook errors through the command-line parser.
            source_sheet = source_workbook.active
            headers = next(
                source_sheet.iter_rows(
                    min_row=1,
                    max_row=1,
                    values_only=True,
                )
            )
        finally:
            # Close the input workbook even if reading the headers fails.
            source_workbook.close()

        # Ensure the workbook contains columns beyond the metadata columns.
        if len(headers) <= METADATA_COLUMN_COUNT:
            parser.error(
                "Input workbook has no condition columns after "
                "the first eight metadata columns."
            )

        # Identify condition names from the header row dynamically.
        # Ignore empty headers and remove surrounding whitespace.
        # This avoids hardcoding the number or names of disease conditions.
        conditions = [
            str(header).strip()
            for header in headers[METADATA_COLUMN_COUNT:]
            if header is not None and str(header).strip()
        ]

        # Stop if no valid condition names were found.
        if not conditions:
            parser.error("No condition columns were found.")

        # Use the user-specified output path when provided.
        # Otherwise, create a filename based on the input workbook's name.
        output_path = (
            Path(args.output)
            if args.output
            else input_path.with_name(
                f"{input_path.stem}_confusion_matrix.xlsx"
            )
        )

        # Prevent accidentally overwriting the input workbook.
        if input_path.resolve() == output_path.resolve():
            parser.error("Input and output paths must be different.")

        # Generate the formatted workbook using the detected conditions.
        create_output_workbook(conditions, output_path)

        # Display a summary of the completed local processing workflow.
        print(f"Input workbook: {input_path}")
        print(f"Conditions found: {len(conditions)}")
        print(f"Output workbook created: {output_path}")
        print(
            "Note: confusion-matrix counts have not been calculated."
        )

    # Report common file and workbook errors through the command-line parser.
    except (
        OSError,
        ValueError,
        openpyxl.utils.exceptions.InvalidFileException,
    ) as exc:
        parser.error(f"Could not process the Excel workbook: {exc}")


# Run the program only when this file is executed directly.
if __name__ == "__main__":
    main()
