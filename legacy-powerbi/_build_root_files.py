import json
import uuid
from pathlib import Path

ROOT = Path(__file__).parent

sm_platform = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": "ChurnCast"},
    "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
}
(ROOT / "ChurnCast.SemanticModel" / ".platform").write_text(json.dumps(sm_platform, indent=2), encoding="utf-8")

pbism = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2",
    "settings": {},
}
(ROOT / "ChurnCast.SemanticModel" / "definition.pbism").write_text(json.dumps(pbism, indent=2), encoding="utf-8")

pbip = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": "ChurnCast.Report"}}],
    "settings": {"enableAutoRecovery": True},
}
(ROOT / "ChurnCast.pbip").write_text(json.dumps(pbip, indent=2), encoding="utf-8")

(ROOT / ".gitignore").write_text(
    "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n__pycache__/\n", encoding="utf-8"
)

print("done")
