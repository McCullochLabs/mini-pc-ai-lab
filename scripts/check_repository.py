"""Offline structure, relative-link, JSON and privacy-pattern checks.

Heuristics aid review; passing is not a guarantee of safe publication.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = json.loads((ROOT / 'publication-files.json').read_text(encoding='utf-8'))


def check():
    errors = [f'missing: {name}' for name in REQUIRED if not (ROOT / name).is_file()]
    checked = 0
    patterns = {
        'Windows personal path': r'(?i)[a-z]:[\\/]Users[\\/]',
        'private network': r'\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b',
        'private key': r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
        'token pattern': r'\b(?:ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{25,})\b',
        'cloud or GitHub token': r'\b(?:AKIA[A-Z0-9]{16}|github_pat_[A-Za-z0-9_]{25,})\b',
        'Unix personal path': r'/(?:home|Users)/[A-Za-z0-9_.-]+/',
    }
    for name in REQUIRED:
        path = ROOT / name
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or any(p in ('.local', 'local', 'work', '.git', '.venv', '__pycache__') for p in rel.parts):
            errors.append(f'{name}: invalid publication selection')
            continue
        if not path.is_file(): continue
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            errors.append(f'{rel}: linked or outside-root file')
            continue
        content = path.read_text(encoding='utf-8-sig')
        checked += 1
        if path.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', content):
                link = link.split('#', 1)[0].strip('<>')
                if not link or re.match(r'[a-zA-Z]+:', link):
                    continue
                target = (path.parent / link).resolve()
                if not target.is_relative_to(ROOT) or not target.exists() or target.is_file() and target.relative_to(ROOT).as_posix() not in REQUIRED:
                    errors.append(f'{rel}: broken/outside relative link: {link}')
        if path.suffix == '.json':
            try:
                json.loads(content, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
            except ValueError:
                errors.append(f'{rel}: invalid JSON')
        for label, pattern in patterns.items():
            if re.search(pattern, content):
                errors.append(f'{rel}: review {label}')
    for error in errors:
        print(error)
    print(f'{checked} public text files checked; {len(errors)} issues. Manual privacy review still required.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(check())
