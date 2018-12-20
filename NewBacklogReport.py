from datetime import date
from business_analytics.workbench import WorkBench
from business_analytics.color_print import prGreen


if __name__ == "__main__":
    start = date(2017, 12, 1)  # year, month, day
    end = date(2018, 11, 30)  # year, month, day

    wb = WorkBench(start_date=start, end_date=end)

    prGreen("Starting snapshot process...")
    wb.snapshot()

    prGreen("\nStarting analysis process...")
    wb.analysis_data()

    prGreen("\nGenerating excel reports...")
    wb.report()
