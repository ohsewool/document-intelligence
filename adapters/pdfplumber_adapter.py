"""Re-export of `document_intelligence.adapters.pdfplumber`.

The implementation moved under the package. A top-level `adapters` is a name
other installed distributions also claim - agent-safety-core ships one - and
whichever is a regular package earliest on `sys.path` wins with no warning, so
this module is not a reliable place to import from:

    pip install agent-safety-core --target /tmp/asc
    PYTHONPATH=/tmp/asc python3 -c "from adapters.pdfplumber_adapter import parse_pdf"
    ModuleNotFoundError: No module named 'adapters.pdfplumber_adapter'

It is kept because the README documented this path and a working import should
not break for readers who have no such collision. New code should use
`document_intelligence.adapters.pdfplumber`.
"""

from document_intelligence.adapters.pdfplumber import (  # noqa: F401
    ORDER_BASIS,
    ParseResult,
    SkippedRegion,
    classify,
    parse_pdf,
)

__all__ = ["ORDER_BASIS", "ParseResult", "SkippedRegion", "classify", "parse_pdf"]
