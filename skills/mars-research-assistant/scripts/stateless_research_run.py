#!/usr/bin/env python3
"""One-shot source selection and batch field acquisition for research runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence


AVAILABLE = "available"
LONGBRIDGE = "longbridge"
PORTABLE = "portable"
OFFICIAL = "official"
SOURCE_CHOICE_REQUIRED = "source_choice_required"
COMPLETE = "complete"
BLOCKED = "blocked"


# The seam accepts only public research datasets.  This boundary prevents a
# provider implementation from receiving account, position, or order requests.
PUBLIC_RESEARCH_FIELDS = frozenset(
    {
        "macro_event_brief",
        "macro_events",
        "treasury_2y",
        "treasury_10y",
        "treasury_30y",
        "vix",
        "vix3m",
        "dxy",
        "wti",
        "gold",
        "hyg_lqd_history",
        "ndx_rut_history",
        "market_quote",
        "instrument_identity",
        "instrument_profile",
        "business_segments",
        "quarterly_financials",
        "annual_financials",
        "cash_flow",
        "balance_sheet",
        "valuation",
        "finance_calendar",
        "industry_analysis",
        "industry_events",
        "company_events",
        "adjusted_daily_ohlcv",
    }
)
PRIVATE_BROKER_FIELD_PREFIXES = (
    "account",
    "holding",
    "order",
    "position",
    "portfolio",
    "credential",
    "token",
)


@dataclass(frozen=True)
class LongbridgeAvailability:
    """The only Longbridge state a research run is allowed to expose."""

    cli_present: bool
    authorized: bool

    def as_dict(self) -> dict[str, bool]:
        return {"cli_present": self.cli_present, "authorized": self.authorized}


@dataclass(frozen=True)
class FieldValue:
    """A normalized decision field returned by one provider batch."""

    name: str
    status: str
    value: Any
    source: str
    as_of: str

    def is_available(self) -> bool:
        return (
            self.status == AVAILABLE
            and bool(self.source.strip())
            and bool(self.as_of.strip())
        )


@dataclass(frozen=True)
class ResearchRequest:
    """The current request only; it intentionally has no runtime identifier."""

    required_fields: tuple[str, ...]
    source_choice: str | None = None
    delivery: str | None = None
    research_as_of: str | None = None

    def __post_init__(self) -> None:
        if not self.required_fields:
            raise ValueError("required_fields_empty")
        if len(set(self.required_fields)) != len(self.required_fields):
            raise ValueError("required_fields_duplicate")
        if any(_is_private_broker_field(field) for field in self.required_fields):
            raise ValueError("private_field_not_allowed")
        if any(field not in PUBLIC_RESEARCH_FIELDS for field in self.required_fields):
            raise ValueError("public_field_not_allowed")
        if self.source_choice not in {None, LONGBRIDGE, PORTABLE}:
            raise ValueError("source_choice_invalid")
        if self.delivery not in {None, "macro_regime"}:
            raise ValueError("delivery_invalid")


@dataclass(frozen=True)
class ResearchRunResult:
    """Observable one-shot result for the stateless research-run seam."""

    status: str
    profile: str | None
    longbridge: dict[str, bool]
    fields: tuple[FieldValue, ...]
    missing_fields: tuple[str, ...]
    validation_blockers: tuple[str, ...] = ()
    markdown: str | None = None
    board_html: str | None = None


class BatchProvider(Protocol):
    """A provider that receives all currently unresolved fields in one request."""

    def fetch_many(self, fields: tuple[str, ...]) -> Mapping[str, FieldValue]: ...


class XNYSSessionCalendar(Protocol):
    """Supplies completed XNYS sessions for one explicit research reference time."""

    def completed_sessions(self, research_as_of: str) -> Sequence[str]: ...


class PrimaryEventSourceRegistry(Protocol):
    """Approves one exact event against its primary evidence record."""

    def approves(self, event: Mapping[str, Any]) -> bool: ...


class SourceUnavailable(Exception):
    """A recoverable source-level failure eligible for the configured fallback."""


CommandRunner = Callable[[Sequence[str]], tuple[int, str]]
Which = Callable[[str], Optional[str]]


def preflight_longbridge(
    *,
    which: Which = shutil.which,
    command_runner: CommandRunner | None = None,
) -> LongbridgeAvailability:
    """Read only CLI/token validity; never return command output or account data."""

    if which("longbridge") is None:
        return LongbridgeAvailability(cli_present=False, authorized=False)

    runner = command_runner or _run_status_command
    try:
        code, output = runner(("longbridge", "auth", "status", "--format", "json"))
    except (OSError, subprocess.TimeoutExpired):
        return LongbridgeAvailability(cli_present=True, authorized=False)
    if code != 0:
        return LongbridgeAvailability(cli_present=True, authorized=False)
    return LongbridgeAvailability(
        cli_present=True,
        authorized=_authorization_is_valid(output),
    )


def run_stateless_research(
    request: ResearchRequest,
    *,
    availability: LongbridgeAvailability,
    providers: Mapping[str, BatchProvider],
    session_calendar: XNYSSessionCalendar | None = None,
    primary_event_source_registry: PrimaryEventSourceRegistry | None = None,
) -> ResearchRunResult:
    """Resolve one request through the selected source profile without persistence."""

    if request.source_choice is None and availability.cli_present and availability.authorized:
        return ResearchRunResult(
            status=SOURCE_CHOICE_REQUIRED,
            profile=None,
            longbridge=availability.as_dict(),
            fields=(),
            missing_fields=request.required_fields,
        )

    profile, source_order = _source_order(request.source_choice, availability)
    resolved, validation_blockers = _resolve_fields(
        request.required_fields,
        source_order,
        providers,
        _macro_ratio_pair_validation(request, session_calendar),
    )
    missing = tuple(field for field in request.required_fields if field not in resolved)
    fields = tuple(resolved[field] for field in request.required_fields if field in resolved)
    result = ResearchRunResult(
        status=COMPLETE if not missing else BLOCKED,
        profile=profile,
        longbridge=availability.as_dict(),
        fields=fields,
        missing_fields=missing,
        validation_blockers=validation_blockers,
    )
    if request.delivery == "macro_regime":
        return _attach_macro_delivery(
            result,
            request.research_as_of,
            session_calendar,
            primary_event_source_registry,
        )
    return result


def _source_order(
    source_choice: str | None,
    availability: LongbridgeAvailability,
) -> tuple[str, tuple[str, ...]]:
    if source_choice == LONGBRIDGE and availability.cli_present and availability.authorized:
        return LONGBRIDGE, (LONGBRIDGE, PORTABLE, OFFICIAL)
    return PORTABLE, (PORTABLE, OFFICIAL)


def _is_private_broker_field(field: str) -> bool:
    return field.startswith(PRIVATE_BROKER_FIELD_PREFIXES)


def _resolve_fields(
    required_fields: tuple[str, ...],
    source_order: tuple[str, ...],
    providers: Mapping[str, BatchProvider],
    validation_problems: Callable[[FieldValue], tuple[str, ...]] | None = None,
) -> tuple[dict[str, FieldValue], tuple[str, ...]]:
    unresolved = required_fields
    resolved: dict[str, FieldValue] = {}
    rejected: dict[str, tuple[str, ...]] = {}
    for source in source_order:
        if not unresolved:
            break
        provider = providers.get(source)
        if provider is None:
            continue
        try:
            response = provider.fetch_many(unresolved)
        except SourceUnavailable:
            continue
        for name in unresolved:
            value = response.get(name)
            if (
                value is not None
                and value.name == name
                and value.is_available()
            ):
                problems = validation_problems(value) if validation_problems else ()
                if not problems:
                    resolved[name] = value
                else:
                    rejected[name] = problems
        unresolved = tuple(name for name in unresolved if name not in resolved)
    blockers = tuple(
        problem
        for name in unresolved
        for problem in rejected.get(name, ())
    )
    return resolved, blockers


def _macro_ratio_pair_validation(
    request: ResearchRequest,
    session_calendar: XNYSSessionCalendar | None,
) -> Callable[[FieldValue], tuple[str, ...]] | None:
    if request.delivery != "macro_regime":
        return None
    from macro_delivery import ratio_pair_validation_problems

    def validation_problems(field: FieldValue) -> tuple[str, ...]:
        return ratio_pair_validation_problems(
            field,
            research_as_of=request.research_as_of,
            session_calendar=session_calendar,
        )

    return validation_problems


def _attach_macro_delivery(
    result: ResearchRunResult,
    research_as_of: str | None,
    session_calendar: XNYSSessionCalendar | None,
    primary_event_source_registry: PrimaryEventSourceRegistry | None,
) -> ResearchRunResult:
    from macro_delivery import build_macro_delivery

    delivery = build_macro_delivery(
        {field.name: field for field in result.fields},
        research_as_of=research_as_of,
        session_calendar=session_calendar,
        primary_event_source_registry=primary_event_source_registry,
    )
    upstream_blockers = tuple(
        blocker
        for blocker in result.validation_blockers
        if blocker not in delivery.blockers
    )
    missing = tuple(
        dict.fromkeys(
            (
                *result.missing_fields,
                *result.validation_blockers,
                *delivery.blockers,
            )
        )
    )
    markdown = delivery.markdown
    if upstream_blockers:
        markdown += "\n" + "\n".join(
            f"- data_gap: {blocker}" for blocker in upstream_blockers
        )
    return ResearchRunResult(
        status=COMPLETE if not missing else BLOCKED,
        profile=result.profile,
        longbridge=result.longbridge,
        fields=result.fields,
        missing_fields=missing,
        validation_blockers=result.validation_blockers,
        markdown=markdown,
        board_html=delivery.board_html,
    )


def _run_status_command(command: Sequence[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return completed.returncode, completed.stdout


def _authorization_is_valid(output: str) -> bool:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, Mapping):
        return False

    for key in ("authorized", "authenticated", "token_valid", "valid"):
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    status = payload.get("status")
    return isinstance(status, str) and status.lower() in {"active", "authorized", "valid"}
