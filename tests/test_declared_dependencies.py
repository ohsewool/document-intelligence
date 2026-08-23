"""`dependencies = []`가 참인가.

`pyproject.toml`은 이렇게 말한다.

    dependencies = []

**"설치하면 아무것도 딸려오지 않는다"는 이 저장소의 주장이다.** 증거 모델을 쓰는
쪽이 파서를 고를 수 있다는 뜻이고, 배포 결정을 바꾸는 사실이다. 그 주장은 소스가
표준 라이브러리 밖의 것을 **모듈 수준에서** import하지 않을 때만 참이다.

예외가 하나 있다. `adapters/pdfplumber.py`의 `parse_pdf`가 `pdfplumber`를 **함수
안에서** import한다. 함수 안에 있는 이유가 정확히 이 주장이다 — 모듈 수준으로
올리면 pdfplumber가 없는 곳에서 **import만으로 패키지 전체가 죽는다.**

**이 검사는 형제 저장소에 있었고 여기에는 없었다.** `mcp-gateway`가 자기
`dependencies = []`에 대해 같은 것을 지키고, `rag-profile-selector`는
`test_optional_sibling.py`가 형제 없이 스위트를 돌려 확인한다. 셋이 같은 주장을
하는데 **둘만 지키고 있었다** — 이 포트폴리오가 반복해서 찾아온 모양이다: 규칙을
세우고 한 곳에 적용한 뒤 나머지를 세어보지 않는 것.

2026-08-23에 다섯 저장소의 자기검사를 표로 만들다 나왔다.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "document_intelligence"

# 함수 안에서 부르는 것이 허용된 바깥 이름. **이름으로 둔다** — 하한선이 아니라
# 정확한 집합이라야 새로 하나 들어오는 것도, 없어지는 것도 걸린다.
LAZY_OUTSIDE = {"pdfplumber"}


def declared_dependencies() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^dependencies\s*=\s*(\[[^\]]*\])", text, re.MULTILINE | re.DOTALL)
    assert match, "pyproject.toml에서 `dependencies`를 찾지 못했다 — 형식이 바뀌었으면 이 검사는 아무것도 확인하지 않는다"
    return match.group(1)


def module_level_imports():
    """소스 파일들이 **모듈 수준에서** 들여오는 이름."""
    found = {}
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:                       # 최상위만. 함수 안은 세지 않는다
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                found.setdefault(name, []).append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return found


class TestTheClaimItself:
    def test_pyproject_still_declares_nothing(self):
        assert declared_dependencies().strip() == "[]", (
            "`dependencies`가 더 이상 비어 있지 않다. 그건 괜찮을 수 있지만, "
            "README와 이 파일의 설명이 함께 바뀌어야 한다.")

    def test_nothing_outside_the_standard_library_is_imported_at_module_level(self):
        outside = {}
        local = {"document_intelligence"}
        for name, where in module_level_imports().items():
            if name in sys.stdlib_module_names or name in local or name.startswith("_"):
                continue
            outside[name] = where
        assert outside == {}, (
            "모듈 수준에서 표준 라이브러리 밖의 것을 들여온다. "
            "`dependencies = []`가 거짓이 된다:\n  "
            + "\n  ".join(f"{n}: {', '.join(w)}" for n, w in sorted(outside.items())))

    def test_the_scan_read_real_files(self):
        """대조: 파일을 못 읽으면 위 검사는 빈손으로 통과한다."""
        assert len(list(SOURCE.rglob("*.py"))) >= 5
        assert module_level_imports(), "최상위 import를 하나도 못 찾았다"


class TestTheLazyImportStaysLazy:
    """`pdfplumber`가 함수 안에 남아 있는가.

    이것이 이 파일의 요점이다. 위 검사는 "지금 모듈 수준에 없다"를 보고, 이 검사는
    **왜 없어야 하는지**를 그 자리에 묶는다.
    """

    def lazy_imports_of(self, name):
        found = []
        for path in sorted(SOURCE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for node in ast.walk(function):
                    imported = []
                    if isinstance(node, ast.Import):
                        imported = [a.name.split(".")[0] for a in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported = [node.module.split(".")[0]]
                    if name in imported:
                        found.append(f"{path.relative_to(ROOT)}:{node.lineno} ({function.name})")
        return found

    @pytest.mark.parametrize("name", sorted(LAZY_OUTSIDE))
    def test_it_is_imported_inside_a_function(self, name):
        assert self.lazy_imports_of(name), (
            f"`{name}`을 함수 안에서 들여오는 곳이 없다. 모듈 수준으로 옮겼다면 "
            "`dependencies = []`가 거짓이다.")

    def test_the_lazy_set_is_exactly_what_we_named(self):
        """새 선택적 의존이 조용히 생기면 걸린다. **하한선이 아니라 이름이다.**"""
        actual = set()
        for path in sorted(SOURCE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            top = {id(node) for node in tree.body}
            for node in ast.walk(tree):
                if id(node) in top:
                    continue
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if (name not in sys.stdlib_module_names
                            and name != "document_intelligence" and not name.startswith("_")):
                        actual.add(name)
        assert actual == LAZY_OUTSIDE, (
            f"함수 안에서 들여오는 바깥 이름이 바뀌었다.\n"
            f"  새로 생김: {sorted(actual - LAZY_OUTSIDE) or '없음'}\n"
            f"  이제 안 씀: {sorted(LAZY_OUTSIDE - actual) or '없음'}")


class TestItImportsWithoutTheParser:
    """**말이 아니라 해보는 쪽.** pdfplumber를 실제로 없애고 import한다.

    위 검사들은 소스를 읽는다. 소스를 읽는 검사는 "모듈 수준에 없다"는 것까지만
    말하고, 예를 들어 `__init__.py`가 어댑터 모듈을 끌어와 그 안에서 무언가가
    터지는 경우는 못 본다. 그래서 한 번은 **정말로 없는 채로** 돌려본다.

    `ModuleNotFoundError`를 낸다 — 맨 `ImportError`가 아니라. 파이썬이 없는 모듈에
    대해 내는 것이 그것이고, `importorskip`이 잡도록 쓰인 것도 그것이다. 형제
    저장소가 첫 시도에서 그 차이로 **하네스가 만든 오류를 결함으로 읽을 뻔했다.**
    """

    def run_without(self, name, code):
        """`src`를 **명시적으로** 경로에 넣는다.

        처음엔 안 넣었다. 로컬에서는 통과했고 CI에서 빨간불이었다 —
        `ModuleNotFoundError: No module named 'document_intelligence'`. 로컬은
        패키지가 설치돼 있어 하위 프로세스가 그것을 집었고, CI는 아니었다.
        **설치 여부에 기대는 검사는 기계마다 다른 것을 시험한다.**

        덤으로 하나 더 지킨다: 하위 프로세스가 집은 것이 **이 저장소의 소스**인지.
        설치된 옛 사본을 집으면 검사는 초록불인데 여기 코드는 안 봤다는 뜻이다 —
        `test_adapter_import_path.py`가 걱정하는 것과 같은 종류의 착각이다.
        """
        script = textwrap.dedent(f'''
            import sys
            sys.path.insert(0, {str(ROOT / "src")!r})
            from importlib.abc import MetaPathFinder

            class Absent(MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == "{name}" or fullname.startswith("{name}."):
                        raise ModuleNotFoundError(
                            f"No module named {{fullname!r}}", name=fullname)
                    return None

            sys.meta_path.insert(0, Absent())
        ''') + textwrap.dedent(code)
        return subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                              capture_output=True, text=True, timeout=180)

    def test_the_subprocess_uses_this_repositorys_source(self):
        """대조: 하위 프로세스가 딴 사본을 보고 있으면 아래 검사들은 딴 코드를
        확인한 것이다."""
        finished = self.run_without("pdfplumber", '''
            import document_intelligence
            print(document_intelligence.__file__)
        ''')
        assert finished.returncode == 0, finished.stderr[-1500:]
        assert finished.stdout.strip().startswith(str(ROOT / "src")), finished.stdout

    def test_the_package_imports(self):
        finished = self.run_without("pdfplumber", '''
            import document_intelligence
            print("ok")
        ''')
        assert finished.returncode == 0, finished.stderr[-1500:]
        assert "ok" in finished.stdout

    def test_the_adapter_module_imports_too(self):
        """어댑터 **모듈**은 열려야 한다. 그 안의 `parse_pdf`만 파서를 필요로 한다."""
        finished = self.run_without("pdfplumber", '''
            from document_intelligence.adapters import pdfplumber as adapter
            print(adapter.parse_pdf.__name__)
        ''')
        assert finished.returncode == 0, finished.stderr[-1500:]
        assert "parse_pdf" in finished.stdout

    def test_calling_the_parser_is_what_fails(self):
        """**되돌림 방향.** 파서를 없앴는데 아무것도 실패하지 않으면, 위 둘은
        차단이 걸리지 않은 상태를 확인한 것이다."""
        finished = self.run_without("pdfplumber", '''
            from document_intelligence.adapters.pdfplumber import parse_pdf
            try:
                parse_pdf("nonexistent.pdf")
            except ModuleNotFoundError as error:
                print("blocked:", error.name)
            except Exception as error:
                print("other:", type(error).__name__)
        ''')
        assert finished.returncode == 0, finished.stderr[-1500:]
        assert "blocked: pdfplumber" in finished.stdout, finished.stdout

    def test_the_harness_really_blocks(self):
        """대조: 차단기가 안 걸리면 위 세 검사는 아무것도 확인하지 않는다."""
        finished = self.run_without("pdfplumber", '''
            try:
                import pdfplumber
                print("NOT BLOCKED")
            except ModuleNotFoundError:
                print("blocked")
        ''')
        assert "blocked" in finished.stdout and "NOT BLOCKED" not in finished.stdout
