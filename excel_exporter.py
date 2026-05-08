from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from src.sla_calculator import SLACalculator


class ExcelExporter:
    CUSTOM_FIELDS = [
        "Sprint",
        "SQUAD",
        "Categoria Incidente",
        "Cliente",
        "Origem Incidente",
        "SLA Incidente",
    ]

    def __init__(self):
        self.sla_calc = SLACalculator()

    @staticmethod
    def _ms_to_str(ms: str) -> str:
        if not ms:
            return ""
        try:
            return datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    @staticmethod
    def _get_custom_field_value(task: Dict[str, Any], field_name: str) -> str:
        """Extrai o valor de um custom field pelo nome."""
        for cf in task.get("custom_fields", []):
            if cf.get("name", "").strip().lower() == field_name.strip().lower():
                value = cf.get("value")
                cf_type = cf.get("type")

                if value is None:
                    return ""

                # Drop down - precisa pegar o nome da opção
                if cf_type == "drop_down":
                    options = cf.get("type_config", {}).get("options", [])
                    for opt in options:
                        if opt.get("orderindex") == value or opt.get("id") == value:
                            return opt.get("name", "")
                    return ""

                # Labels (multi)
                if cf_type == "labels":
                    options = cf.get("type_config", {}).get("options", [])
                    if isinstance(value, list):
                        labels = []
                        for v in value:
                            for opt in options:
                                if opt.get("id") == v:
                                    labels.append(opt.get("label", ""))
                        return ", ".join(labels)

                # Users
                if cf_type == "users":
                    if isinstance(value, list):
                        return ", ".join([u.get("username", "") for u in value])

                # Date
                if cf_type == "date":
                    try:
                        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        return str(value)

                return str(value)

        return ""

    def export(self, tasks: List[Dict[str, Any]], output_path: str) -> str:
        rows = []

        for task in tasks:
            row = {
                "id": task.get("id"),
                "name": task.get("name"),
                "status": (task.get("status") or {}).get("status", ""),
                "date_created": self._ms_to_str(task.get("date_created")),
                "date_updated": self._ms_to_str(task.get("date_updated")),
                "priority": (task.get("priority") or {}).get("priority", "") if task.get("priority") else "",
                "url": task.get("url"),
            }

            for cf_name in self.CUSTOM_FIELDS:
                row[f"cf_{cf_name}"] = self._get_custom_field_value(task, cf_name)

            # SLA calculado em horas úteis
            row["sla_horas_uteis"] = self.sla_calc.calculate_sla(task.get("date_created"))

            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_excel(output_path, index=False, engine="openpyxl")

        return output_path