"""Create a review ZIP without private evidence or scratch artifacts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'Mini-PC-AI-Lab-review.zip'
EXCLUDED = {'.local', 'local', 'work', '.git', '.venv', '__pycache__'}


def main():
    files = []
    selected = json.loads((ROOT / 'publication-files.json').read_text(encoding='utf-8'))
    for name in selected:
        rel = Path(name)
        path = ROOT / rel
        if rel.is_absolute() or '..' in rel.parts or any(part in EXCLUDED for part in rel.parts):
            raise ValueError(f'invalid publication selection: {rel}')
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'linked/outside-root file cannot be packaged: {rel}')
        files.append(path)
    with ZipFile(OUTPUT, 'w', compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert not any(any(p in EXCLUDED for p in Path(name).parts) for name in archive.namelist())
        for path in files:
            assert archive.read(str(Path(ROOT.name) / path.relative_to(ROOT)).replace('\\', '/')) == path.read_bytes()
    print(f'{len(files)} reviewed-source files packaged; private directories excluded.')


if __name__ == '__main__':
    main()
