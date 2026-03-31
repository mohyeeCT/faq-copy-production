import gspread
import gspread.utils
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_gspread_client(sa_info: dict) -> gspread.Client:
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


def load_sheet(gc: gspread.Client, sheet_url: str, worksheet_name: str = None):
    spreadsheet = gc.open_by_url(sheet_url)
    if worksheet_name:
        ws = spreadsheet.worksheet(worksheet_name)
    else:
        ws = spreadsheet.get_worksheet(0)
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    return df, spreadsheet, ws


def write_results_to_sheet(ws, results_df: pd.DataFrame, col_map: dict):
    """Batch write results back to sheet using values_batch_update.
    col_map: {results_df_column_name: sheet_header_name}
    Never writes cell-by-cell.
    """
    headers = ws.row_values(1)

    col_indices = {}
    for df_col, sheet_col in col_map.items():
        if sheet_col in headers:
            col_indices[df_col] = headers.index(sheet_col) + 1
        else:
            new_idx = len(headers) + 1
            ws.update_cell(1, new_idx, sheet_col)
            headers.append(sheet_col)
            col_indices[df_col] = new_idx

    updates = []
    for row_num, (_, row) in enumerate(results_df.iterrows(), start=2):
        for df_col, col_idx in col_indices.items():
            val = row.get(df_col, "")
            if val is None or (isinstance(val, float) and pd.isna(val)):
                val = ""
            updates.append({
                "range": gspread.utils.rowcol_to_a1(row_num, col_idx),
                "values": [[str(val)]]
            })

    if updates:
        ws.spreadsheet.values_batch_update({
            "valueInputOption": "RAW",
            "data": updates
        })
