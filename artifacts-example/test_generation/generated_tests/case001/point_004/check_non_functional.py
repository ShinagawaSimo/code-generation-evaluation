import json
from pathlib import Path

environment = json.loads(Path('environment.json').read_text(encoding='utf-8'))
assertions = json.loads(Path('assertions.json').read_text(encoding='utf-8'))
print({'environment': environment, 'assertions': assertions})
