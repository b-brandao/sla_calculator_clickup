import os
import sys
from dotenv import load_dotenv
from src.clickup_client import ClickUpClient
from src.excel_exporter import ExcelExporter


def main():
    load_dotenv()

    api_token = os.getenv("CLICKUP_API_TOKEN")
    list_id = os.getenv("CLICKUP_LIST_ID")
    output_file = os.getenv("OUTPUT_FILE", "tasks_export.xlsx")

    if not api_token or not list_id:
        print("ERRO: Configure CLICKUP_API_TOKEN e CLICKUP_LIST_ID no arquivo .env")
        sys.exit(1)

    print(f"🔍 Buscando tasks abertas sem subtasks na lista {list_id}...")

    client = ClickUpClient(api_token)
    try:
        tasks = client.get_open_tasks_without_subtasks(list_id)
    except Exception as e:
        print(f"❌ Erro ao buscar tasks: {e}")
        sys.exit(1)

    print(f"✅ {len(tasks)} tasks encontradas.")

    if not tasks:
        print("Nenhuma task para exportar.")
        return

    print("📊 Gerando arquivo Excel...")
    exporter = ExcelExporter()
    path = exporter.export(tasks, output_file)

    print(f"🎉 Arquivo gerado com sucesso: {path}")


if __name__ == "__main__":
    main()