from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db import models
from app.db.session import get_db
import tempfile
import pandas as pd
import json
import re

router = APIRouter()

def clean_text_report(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"(?m)^[ \t]{1,12}", "", text)                  # soft dedent (fix alignment)
    text = re.sub(r"\\(.?)\\*", r"\1", text)                  # strip **bold**
    text = re.sub(r"(?m)^\*\s+", "- ", text)                      # * bullets → - bullets
    text = re.sub(r"\n{3,}", "\n\n", text)                        # collapse blank lines
    def _hdr(m):
        title, underline = m.group(1).strip(), m.group(2)
        return f"{title.upper()}\n{'='*len(title)}" if underline.startswith("=") \
               else f"{title}\n{'-'*len(title)}"
    text = re.sub(r"(?m)^([^\n]+)\n([=\-]{3,})\s*$", _hdr, text)  # normalize underline headers
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)                    # remove leading #
    text = re.sub(r"[ \t]{2,}", " ", text)                        # compress inner spaces
    return text.strip() + "\n"


@router.get("/{key}")
def get_report(key: str, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.key == key).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # Create temp file for response
    if report.type == models.ReportType.PDF:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        with open(tmp_file.name, "w", encoding="utf-8") as f:
            raw = report.value if isinstance(report.value, str) else report.value.decode("utf-8", errors="ignore")
            f.write(clean_text_report(raw))

        return FileResponse(
            tmp_file.name,
            media_type="text/plain",
            filename=f"{report.file_name}"
        )

    elif report.type == models.ReportType.CSV:
        # Assume report.value is JSON or dict-like data
        try:
            report_data = json.loads(report.value)
            df = pd.DataFrame(report_data)  # if it's dict/list
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Invalid CSV data format in DB")

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(tmp_file.name, index=False)

        return FileResponse(
            tmp_file.name,
            media_type="text/csv",
            filename=f"{report.file_name}"
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report type: {report.type}")