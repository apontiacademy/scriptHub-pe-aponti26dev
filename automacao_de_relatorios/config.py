import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class MoodleConfig:
    username: str
    password: str
    report_download_path: Path 
    headless: bool
    students_csv: Path  
    report_analysis_output_csv: Path
    login_url: str
    report_urls: list[str]
    export_report_analysis: bool
    export_report_analysis_path: Optional[Path] 


@dataclass
class GsheetsConfig:
    spreadsheet_id: str
    sheet_name: str
    local_backup_path: Path 
    credentials_json_path: Path 


@dataclass
class Config:
    moodle: MoodleConfig
    gsheets: GsheetsConfig

    @staticmethod
    def load() -> "Config":        
        env_data = Config.__load_env()
        settings_data = Config.__load_settings_json()

        moodle_json = settings_data.get("moodle", {})
        gsheets_json = settings_data.get("gsheets", {})

        moodle_config = MoodleConfig(
            username=env_data["moodle_username"],
            password=env_data["moodle_password"],
            report_download_path=BASE_DIR / "data" / "reports",
            headless=True,
            students_csv=BASE_DIR / "data" / "students.csv",
            report_analysis_output_csv=BASE_DIR / "data" / "analysis_output.csv",
            login_url=moodle_json["loginUrl"],
            report_urls=list(map(lambda i: i.strip(), moodle_json["reportUrls"])),
            export_report_analysis=moodle_json["exportReportAnalysis"],
            export_report_analysis_path=(
                Path(moodle_json["exportReportAnalysisPath"]) 
                if moodle_json["exportReportAnalysis"] and moodle_json.get("exportReportAnalysisPath")
                else None
            )
        )

        gsheets_config = GsheetsConfig(
            spreadsheet_id=gsheets_json["spreadsheetId"],
            sheet_name=gsheets_json["sheetName"],
            local_backup_path=Path(gsheets_json["localBackupPath"]),
            credentials_json_path=BASE_DIR / "credentials.json"
        )

        return Config(moodle=moodle_config, gsheets=gsheets_config)

    @staticmethod
    def __load_env() -> dict:
        load_dotenv(dotenv_path=BASE_DIR / ".env")
        
        data = {
            "moodle_username": os.getenv("MOODLE_USERNAME"),
            "moodle_password": os.getenv("MOODLE_PASSWORD")
        }

        if not data["moodle_username"] or not data["moodle_password"]:
            raise ValueError("MOODLE_USERNAME e MOODLE_PASSWORD devem ser definidos no arquivo .env")
        return data
        
    @staticmethod
    def __load_settings_json() -> dict:
        settings_path = BASE_DIR / "settings.json"
        
        if not settings_path.exists():
            raise FileNotFoundError(f"O arquivo {settings_path} não foi encontrado.")
            
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data