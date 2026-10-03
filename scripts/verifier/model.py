"""Result types and the reporting context shared by every check."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from .loading import read_json_object


class Status(StrEnum):
    PASS = "pass"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class Result:
    status: Status
    check: str
    detail: str


class Reporter:
    def __init__(self):
        self._results: list[Result] = []

    def record(self, status: Status, check: str, detail) -> None:
        self._results.append(Result(status, check, str(detail)))

    @property
    def results(self) -> list[dict]:
        return [asdict(result) for result in self._results]

    def overall(self) -> Status:
        statuses = {result.status for result in self._results}
        if Status.FAILED in statuses:
            return Status.FAILED
        if Status.INCONCLUSIVE in statuses:
            return Status.INCONCLUSIVE
        return Status.PASS

    @contextmanager
    def failures_as(self, check: str, *errors: type[Exception]):
        """Record any of `errors` raised inside the block as a failed `check` instead of propagating."""
        try:
            yield
        except errors as error:
            self.record(Status.FAILED, check, error)


@dataclass(frozen=True)
class Context:
    root: Path
    reporter: Reporter

    def relative(self, path: Path) -> str:
        return str(path.relative_to(self.root))

    def load_json(self, path: Path) -> dict | None:
        """Read a JSON object, recording a failure and returning None when it is unreadable."""
        try:
            return read_json_object(path)
        except (OSError, ValueError) as error:
            self.reporter.record(Status.FAILED, self.relative(path), error)
            return None
