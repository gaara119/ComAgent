"""Preserve actual D3 integration pytest commands, raw outputs and source hashes."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tests',nargs='+',default=['tests'])
    args=parser.parse_args()
    output=args.output if args.output.is_absolute() else ROOT/args.output
    if output.exists():raise SystemExit('Preserve earlier evidence; select a fresh output path.')
    output.mkdir(parents=True)
    command=[sys.executable,'-B','-m','pytest',*args.tests,'-q','--basetemp',str(ROOT/'.runtime'/('pytest-'+output.name))]
    sources=[ROOT/'qa_agent/pipeline.py',ROOT/'qa_agent/schemas.py',ROOT/'qa_agent/config.py',ROOT/'qa_agent/llm.py',
             ROOT/'qa_agent/sql/generator.py',ROOT/'qa_agent/sql/executor.py',ROOT/'qa_agent/sql/prompts/multi_table.txt',
             ROOT/'qa_agent/sql/validator.py',
             ROOT/'qa_agent/nlu/linker.py',
             ROOT/'ui/app.py',ROOT/'api/main.py',*sorted((ROOT/'qa_agent/clarify').rglob('*.py')),
             *sorted((ROOT/'qa_agent/clarify/prompts').glob('*.txt'))]
    metadata={'command':command,'cwd':str(ROOT),'created_at_utc':datetime.now(timezone.utc).isoformat(),
              'measurement':'actual module tests; AppTest API fixtures are mocks and do not constitute model EX',
              'source_sha256':{str(path.relative_to(ROOT)).replace('\\','/'):sha256(path.read_bytes()).hexdigest() for path in sources}}
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    metadata['exit_code']=result.returncode
    (output/'command.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'pytest.stdout.txt').write_text(result.stdout,encoding='utf-8')
    (output/'pytest.stderr.txt').write_text(result.stderr,encoding='utf-8')
    print(result.stdout,end='')
    if result.stderr:print(result.stderr,file=sys.stderr,end='')
    return result.returncode


if __name__=='__main__':raise SystemExit(main())
