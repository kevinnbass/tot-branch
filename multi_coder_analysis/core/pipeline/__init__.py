from __future__ import annotations

"""Lightweight functional pipeline primitives used by the Tree-of-Thought refactor.

The goal is to decouple algorithmic steps from I/O and orchestration while
remaining extremely small and dependency-free.  Each `Step[T]` receives and
returns the same context object enabling natural chaining and testability.
"""

from typing import Generic, TypeVar, Protocol, Callable, List

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class Step(Generic[T], Protocol):
    """A pure-function processing step.

    Sub-classes implement :py:meth:`run` and **MUST NOT** mutate global state or
    perform side-effects outside the provided context object.
    """

    def run(self, ctx: T) -> T:  # noqa: D401
        """Transform *ctx* and return it (or a *new* instance).
        
        The default Tree-of-Thought implementation mutates the context in-place
        and returns the same object for convenience.
        """
        raise NotImplementedError


class FunctionStep(Generic[T]):
    """Adapter turning a plain function into a :class:`Step`."""

    def __init__(self, fn: Callable[[T], T]):
        self._fn = fn

    def run(self, ctx: T) -> T:  # type: ignore[override]
        return self._fn(ctx)


class Pipeline(Generic[T]):
    """Composable list of :class:`Step` objects executed sequentially."""

    def __init__(self, steps: List[Step[T]]):
        self._steps = steps

    def run(self, ctx: T) -> T:
        for step in self._steps:
            # Allow steps (e.g., answer evaluators) to signal early termination
            if (
                isinstance(ctx, list)
                and ctx
                and all(getattr(c, "is_concluded", False) for c in ctx)
            ) or getattr(ctx, "is_concluded", False):
                break
            ctx = step.run(ctx)
        return ctx


__all__ = [
    "Step",
    "FunctionStep",
    "Pipeline",
] 