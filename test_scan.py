import pandas as pd
from backend.auto_scan import AutoBiasScanner
from dotenv import load_dotenv

load_dotenv()
df = pd.read_csv("biased_dataset.csv")
scanner = AutoBiasScanner()
result = scanner.scan(df)
print(result.get("status"), result.get("message"))
if result.get("status") == "warning":
    print("Roles:", result.get("detected_roles"))
