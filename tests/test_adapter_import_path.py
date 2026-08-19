"""The adapter must be reachable by a name nobody else can claim.

`adapters/pdfplumber_adapter.py` was the documented import, and `adapters` is a
top-level name other installed distributions also ship - agent-safety-core, a
sibling of this repository, ships one. Whichever is a regular package earliest
on `sys.path` wins, with no warning:

    pip install agent-safety-core --target /tmp/asc
    PYTHONPATH=/tmp/asc python3 -c "from adapters.pdfplumber_adapter import parse_pdf"
    ModuleNotFoundError: No module named 'adapters.pdfplumber_adapter'

For a library that exists so a citation can be checked against a document, a
parser that an unrelated project can silently replace is not a small problem.
The implementation now lives at `document_intelligence.adapters.pdfplumber`,
which is inside a package this distribution owns; the old path is kept as a
re-export for readers who have no collision.

The decoy here is built by hand rather than by installing a sibling, so this
suite needs no other repository to test its own imports.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pytest.importorskip("pdfplumber")

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def shadowed(tmp_path):
    """A directory holding a regular top-level `adapters` package of its own.

    Regular, not a bare directory: that is what makes it win rather than merge,
    and it is what an installed distribution actually looks like.
    """
    foreign = tmp_path / "site"
    (foreign / "adapters").mkdir(parents=True)
    (foreign / "adapters" / "__init__.py").write_text(
        '"""Some other project\'s adapters package."""\n', encoding="utf-8")
    return foreign


def run(code: str, *, extra_path: Path | None = None) -> subprocess.CompletedProcess:
    entries = [str(ROOT), str(ROOT / "src")]
    if extra_path is not None:
        entries.insert(0, str(extra_path))
    return subprocess.run([sys.executable, "-c", textwrap.dedent(code)],
                          cwd=ROOT, capture_output=True, text=True,
                          env={"PYTHONPATH": ":".join(entries), "PATH": "/usr/bin:/bin"})


class TestThePackagePathSurvivesAShadowingAdapters:
    def test_the_adapter_imports(self, shadowed):
        result = run("from document_intelligence.adapters.pdfplumber import parse_pdf\n"
                     "print('ok')", extra_path=shadowed)
        assert result.returncode == 0, result.stderr
        assert "ok" in result.stdout

    def test_it_is_this_repositorys_file(self, shadowed):
        result = run("import document_intelligence.adapters.pdfplumber as a\n"
                     "print(a.__file__)", extra_path=shadowed)
        assert Path(result.stdout.strip()) == (
            ROOT / "src" / "document_intelligence" / "adapters" / "pdfplumber.py")

    def test_the_decoy_really_does_take_the_top_level_name(self, shadowed):
        """Pins the premise. Without this, the two tests above would pass in an
        environment where nothing was shadowing anything and would be saying
        nothing at all."""
        result = run("import adapters; print(adapters.__file__)", extra_path=shadowed)
        assert Path(result.stdout.strip()) == shadowed / "adapters" / "__init__.py"

    def test_the_old_path_is_the_one_that_breaks(self, shadowed):
        """Recorded rather than worked around. This is the failure the move
        exists to escape, and it is not fixable from inside this repository -
        the name belongs to whoever is first on the path."""
        result = run("from adapters.pdfplumber_adapter import parse_pdf",
                     extra_path=shadowed)
        assert result.returncode != 0
        assert "ModuleNotFoundError" in result.stderr


class TestTheOldPathStillWorksWhenNothingCollides:
    def test_the_re_export_imports(self):
        result = run("from adapters.pdfplumber_adapter import parse_pdf\nprint('ok')")
        assert result.returncode == 0, result.stderr

    def test_it_is_the_same_function(self):
        """A re-export that drifted into a copy would be worse than removing it."""
        result = run("""
            from adapters.pdfplumber_adapter import parse_pdf as old
            from document_intelligence.adapters.pdfplumber import parse_pdf as new
            print(old is new)
        """)
        assert result.stdout.strip() == "True"

    def test_everything_public_is_re_exported(self):
        """A partial re-export breaks callers one name at a time.

        Compared on what the module *defines*, not on `dir()`: `dir()` also
        lists everything the module imported, so a first version of this failed
        on `Path` and `hashlib`. Filtering by `__module__` - while keeping plain
        constants, which have none - makes the comparison about the public
        surface rather than the import block. Imported *modules* also have no
        `__module__`, so they need excluding separately; that was the second
        version's mistake.
        """
        result = run("""
            import document_intelligence.adapters.pdfplumber as new
            import adapters.pdfplumber_adapter as old
            import inspect
            defined = {
                name for name in dir(new)
                if not name.startswith('_')
                and not inspect.ismodule(getattr(new, name))
                and getattr(getattr(new, name), '__module__', new.__name__) == new.__name__
            }
            print(sorted(defined - set(dir(old))))
        """)
        assert result.stdout.strip() == "[]", result.stdout

    def test_the_comparison_covers_the_names_that_matter(self):
        """Guards the filter above: if `__module__` filtering ever excluded
        everything, the test before this one would pass over an empty set."""
        result = run("""
            import document_intelligence.adapters.pdfplumber as new
            import inspect
            defined = {
                name for name in dir(new)
                if not name.startswith('_')
                and not inspect.ismodule(getattr(new, name))
                and getattr(getattr(new, name), '__module__', new.__name__) == new.__name__
            }
            print(sorted(defined))
        """)
        assert {"parse_pdf", "classify", "ParseResult", "SkippedRegion", "ORDER_BASIS"} <= set(
            eval(result.stdout.strip())), result.stdout
