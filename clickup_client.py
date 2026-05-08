import requests
from typing import List, Dict, Any


class ClickUpClient:
    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_token: str):
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json",
        }

    def get_open_tasks_without_subtasks(self, list_id: str) -> List[Dict[str, Any]]:
        """
        Busca todas as tasks abertas (não fechadas/arquivadas) que NÃO possuem subtasks
        em uma lista específica do ClickUp.
        """
        all_tasks = []
        page = 0

        while True:
            url = f"{self.BASE_URL}/list/{list_id}/task"
            params = {
                "archived": "false",
                "include_closed": "false",
                "subtasks": "true",  # traz todas as tasks (pais e filhas) para identificarmos
                "page": page,
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            tasks = data.get("tasks", [])

            if not tasks:
                break

            all_tasks.extend(tasks)
            page += 1

            if len(tasks) < 100:
                break

        # Identifica IDs de tasks que são pais (têm subtasks)
        parent_ids = {t.get("parent") for t in all_tasks if t.get("parent")}

        # Filtra: somente tasks que NÃO são pais (não estão em parent_ids como pai),
        # que NÃO são subtasks (não possuem campo parent),
        # e que estão abertas
        filtered = []
        for task in all_tasks:
            is_subtask = task.get("parent") is not None
            is_parent = task.get("id") in parent_ids
            status_type = (task.get("status") or {}).get("type", "")

            if not is_subtask and not is_parent and status_type != "closed":
                filtered.append(task)

        return filtered