"""SEC EDGAR adapter utilities."""

from adapters.sec.client import SECClient, SECIdentityConfig, validate_sec_user_agent
from adapters.sec.issuer_registry import IssuerRecord, ingest_company_tickers, parse_company_tickers
from adapters.sec.submissions import SubmissionRecord, ingest_submissions, parse_submissions_recent
from adapters.sec.utils import normalize_cik

__all__ = [
    "IssuerRecord",
    "SECClient",
    "SECIdentityConfig",
    "SubmissionRecord",
    "ingest_company_tickers",
    "ingest_submissions",
    "parse_company_tickers",
    "parse_submissions_recent",
    "normalize_cik",
    "validate_sec_user_agent",
]
