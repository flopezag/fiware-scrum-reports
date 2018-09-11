from datetime import date
from business_analytics.workbench import WorkBench


if __name__ == "__main__":
    start = date(2016, 12, 1)  # year, month, day
    end = date(2017, 11, 30)  # year, month, day

    wb = WorkBench(start_date=start, end_date=end)

    print("Starting snapshot process...")
    wb.snapshot()

    print("Starting analysis process...")
    wb.analysis_data()
