"""
APEX Framework - Core Implementation
Kompakt version för BACOWR integration
Baserad på användarens fullständiga APEX spec
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Generic, Protocol, TypeVar, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

T = TypeVar("T", bound=BaseModel)
C = TypeVar("C")

Context = dict[str, Any]
QualityScore = float


class QualityFunction(Protocol[T]):
    """Protocol för domän-specifika quality functions."""

    def __call__(self, output: T, context: Context) -> QualityScore:
        ...


class TerminationReason(Enum):
    """Anledningar till att execution avslutas."""
    CONVERGED = "converged"
    MAX_ITERATIONS = "max_iterations"
    QUALITY_PLATEAU = "quality_plateau"
    CONSTRAINT_CEILING = "constraint_ceiling"
    VALIDATION_FAILURE = "validation_failure"
    TOKEN_EXHAUSTION = "token_exhaustion"
    NO_CANDIDATES = "no_candidates"
    ROUTING_FAILURE = "routing_failure"
    INTERNAL_ERROR = "internal_error"


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class APEXConfig:
    """Konfiguration för en APEX-instans."""
    quality_threshold: float = 0.85
    severity_threshold: float = 0.3
    plateau_epsilon: float = 0.01
    max_iterations: int = 5
    max_validation_retries: int = 3
    parallel_generators: int = 3
    token_budget_architect: int = 2000
    token_budget_generator: int = 4000
    token_budget_critic: int = 1500
    token_budget_integrator: int = 2000
    model_architect: str = "claude-sonnet-4"
    model_generator: str = "claude-sonnet-4"
    model_critic: str = "claude-haiku"
    routing_method: str = "semantic"


@dataclass
class APEXMetrics:
    """Metrics för observability och diagnostik."""
    tokens_used: int = 0
    api_calls: int = 0
    wall_time_seconds: float = 0.0
    cost_usd: float = 0.0
    final_score: float = 0.0
    score_trajectory: list[float] = field(default_factory=list)
    invariant_violations: int = 0
    iterations_used: int = 0
    termination_reason: TerminationReason = TerminationReason.CONVERGED
    pattern_selected: str = ""
    route_confidence: float = 0.0
    generator_exceptions: int = 0
    critic_exceptions: int = 0


@dataclass
class APEXResult(Generic[T]):
    """Resultat från en APEX execution."""
    output: T | None
    score: float
    iterations: int
    termination_reason: TerminationReason
    metrics: APEXMetrics
    critiques: list[Critique] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return (
            self.output is not None
            and self.termination_reason == TerminationReason.CONVERGED
        )


# ============================================================================
# CRITIQUE SYSTEM
# ============================================================================


@dataclass
class Critique:
    """En specifik kritik av genererad output."""
    dimension: str
    issue: str
    severity: float
    suggestion: str | None = None
    location: str | None = None


@dataclass
class CritiqueResult:
    """Aggregerat resultat från alla critics."""
    critiques: list[Critique]

    @property
    def max_severity(self) -> float:
        if not self.critiques:
            return 0.0
        return max(c.severity for c in self.critiques)

    @property
    def avg_severity(self) -> float:
        if not self.critiques:
            return 0.0
        return sum(c.severity for c in self.critiques) / len(self.critiques)

    def above_threshold(self, threshold: float) -> list[Critique]:
        return [c for c in self.critiques if c.severity >= threshold]


class Critic(ABC, Generic[T]):
    """Bas-klass för domän-specifika critics."""
    dimension: str = "default"
    weight: float = 1.0

    @abstractmethod
    async def evaluate(self, output: T, context: Context) -> list[Critique]:
        """Evaluera output och returnera kritik."""
        ...


# ============================================================================
# GENERATORS
# ============================================================================


class Generator(ABC, Generic[T]):
    """Bas-klass för output-generatorer."""

    @abstractmethod
    async def generate(
        self,
        task: str,
        context: Context,
        constraints: dict[str, Any] | None = None,
    ) -> T:
        """Generera output baserat på task och context."""
        ...


@dataclass
class GenerationBatch(Generic[T]):
    """Resultat från en batch generering."""
    candidates: list[T]
    exceptions: list[Exception] = field(default_factory=list)

    @property
    def has_candidates(self) -> bool:
        return bool(self.candidates)


class DiverseGeneratorPool(Generic[T]):
    """Pool av generatorer med olika strategier/temperaturer."""

    def __init__(self, generators: list[Generator[T]]):
        if not generators:
            raise ValueError("DiverseGeneratorPool kräver minst en generator")
        self.generators = generators

    async def generate_batch(
        self,
        task: str,
        context: Context,
        n: int | None = None,
    ) -> GenerationBatch[T]:
        """Generera upp till n kandidater parallellt."""
        n = n or len(self.generators)
        selected = self.generators[:n]

        tasks = [g.generate(task, context) for g in selected]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates: list[T] = []
        exceptions: list[Exception] = []

        for r in results:
            if isinstance(r, Exception):
                exceptions.append(r)
            else:
                candidates.append(r)

        return GenerationBatch(candidates=candidates, exceptions=exceptions)


# ============================================================================
# CONVERGENCE STRATEGIES
# ============================================================================


class ConvergenceStrategy(ABC, Generic[T]):
    """Strategi för att konvergera från kandidater till bästa output."""

    @abstractmethod
    async def converge(
        self,
        candidates: list[T],
        context: Context,
        score_fn: QualityFunction[T],
    ) -> tuple[T, QualityScore]:
        ...


class VotingConvergence(ConvergenceStrategy[T]):
    """Score-baserad voting - högsta score vinner."""

    async def converge(
        self,
        candidates: list[T],
        context: Context,
        score_fn: QualityFunction[T],
    ) -> tuple[T, QualityScore]:
        if not candidates:
            raise ValueError("VotingConvergence kräver minst en kandidat")

        best: T = candidates[0]
        best_score: float = score_fn(best, context)

        for c in candidates[1:]:
            s = score_fn(c, context)
            if s > best_score:
                best, best_score = c, s

        return best, best_score


# ============================================================================
# ROUTING
# ============================================================================


class PatternType(Enum):
    """Tillgängliga APEX patterns."""
    DIRECT = "direct"
    FRACTAL_DECOMPOSITION = "fractal_decomposition"
    ADVERSARIAL_REFINEMENT = "adversarial_refinement"
    CAPABILITY_CASCADE = "capability_cascade"


@dataclass
class Route:
    """En routing-regel."""
    name: str
    triggers: list[str]
    pattern: PatternType
    confidence_threshold: float = 0.7


class Router(ABC):
    """Bas-klass för task routing."""

    @abstractmethod
    async def select_pattern(
        self,
        task: str,
        context: Context,
    ) -> tuple[PatternType, float]:
        ...


class SemanticRouter(Router):
    """Router baserad på semantic/keyword matching."""

    def __init__(self, routes: list[Route]):
        self.routes = routes

    async def select_pattern(
        self,
        task: str,
        context: Context,
    ) -> tuple[PatternType, float]:
        lowered = task.lower()
        best: PatternType | None = None
        best_conf: float = 0.0

        for route in self.routes:
            hits = sum(1 for t in route.triggers if t.lower() in lowered)
            if not hits:
                continue
            conf = min(1.0, 0.4 + 0.2 * hits)
            if conf > best_conf:
                best_conf = conf
                best = route.pattern

        if best is None:
            return PatternType.CAPABILITY_CASCADE, 0.8

        return best, best_conf


# ============================================================================
# PATTERN IMPLEMENTATIONS
# ============================================================================


class Pattern(ABC, Generic[T]):
    """Bas-klass för execution patterns."""

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Context,
        config: APEXConfig,
        quality_fn: QualityFunction[T],
        output_schema: type[T],
    ) -> APEXResult[T]:
        ...


class DirectPattern(Pattern[T]):
    """Enkel single-shot generation utan orkestrering."""

    def __init__(self, generator: Generator[T]):
        self.generator = generator

    async def execute(
        self,
        task: str,
        context: Context,
        config: APEXConfig,
        quality_fn: QualityFunction[T],
        output_schema: type[T],
    ) -> APEXResult[T]:
        metrics = APEXMetrics(pattern_selected="direct")
        start = time.perf_counter()

        try:
            output = await self.generator.generate(task, context)
            if not isinstance(output, output_schema):
                output = output_schema.model_validate(output)

            score = quality_fn(output, context)
            metrics.final_score = score
            metrics.score_trajectory = [score]
            metrics.iterations_used = 1

            if score >= config.quality_threshold:
                metrics.termination_reason = TerminationReason.CONVERGED
            else:
                metrics.termination_reason = TerminationReason.QUALITY_PLATEAU

            return APEXResult(
                output=output,
                score=score,
                iterations=1,
                termination_reason=metrics.termination_reason,
                metrics=metrics,
            )

        except ValidationError:
            metrics.invariant_violations += 1
            metrics.termination_reason = TerminationReason.VALIDATION_FAILURE
            return APEXResult(
                output=None,
                score=0.0,
                iterations=1,
                termination_reason=TerminationReason.VALIDATION_FAILURE,
                metrics=metrics,
            )
        except Exception:
            metrics.termination_reason = TerminationReason.INTERNAL_ERROR
            return APEXResult(
                output=None,
                score=0.0,
                iterations=1,
                termination_reason=TerminationReason.INTERNAL_ERROR,
                metrics=metrics,
            )
        finally:
            metrics.wall_time_seconds = time.perf_counter() - start


# ============================================================================
# MAIN EXECUTOR
# ============================================================================


class APEXExecutor(Generic[T]):
    """
    Huvudsaklig executor för APEX framework.
    Koordinerar routing, pattern selection, och execution.
    """

    def __init__(
        self,
        router: Router,
        patterns: dict[PatternType, Pattern[T]],
        quality_fn: QualityFunction[T],
        output_schema: type[T],
        config: APEXConfig | None = None,
        domain: str | None = None,
    ):
        self.router = router
        self.patterns = patterns
        self.quality_fn = quality_fn
        self.output_schema = output_schema
        self.config = config or APEXConfig()
        self.domain = domain or "default"

    async def execute(
        self,
        task: str,
        context: Context | None = None,
    ) -> APEXResult[T]:
        """
        Exekvera en task genom APEX framework.
        """
        ctx: Context = context or {}
        metrics_base = APEXMetrics()
        start = time.perf_counter()

        try:
            try:
                pattern_type, confidence = await self.router.select_pattern(task, ctx)
            except Exception:
                pattern_type, confidence = PatternType.CAPABILITY_CASCADE, 0.0

            if pattern_type not in self.patterns:
                pattern_type = PatternType.CAPABILITY_CASCADE

            pattern = self.patterns[pattern_type]

            result = await pattern.execute(
                task=task,
                context=ctx,
                config=self.config,
                quality_fn=self.quality_fn,
                output_schema=self.output_schema,
            )

            result.metrics.route_confidence = confidence
            result.metrics.pattern_selected = (
                result.metrics.pattern_selected or pattern_type.value
            )
            result.metrics.wall_time_seconds = (
                result.metrics.wall_time_seconds or time.perf_counter() - start
            )
            return result

        except Exception:
            metrics_base.termination_reason = TerminationReason.INTERNAL_ERROR
            metrics_base.wall_time_seconds = time.perf_counter() - start
            return APEXResult(
                output=None,
                score=0.0,
                iterations=0,
                termination_reason=TerminationReason.INTERNAL_ERROR,
                metrics=metrics_base,
            )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_apex_instance(
    domain: str,
    output_schema: type[T],
    quality_fn: QualityFunction[T],
    generator_factory: Callable[[], Generator[T]],
    critics: list[Critic[T]],
    config: APEXConfig | None = None,
) -> APEXExecutor[T]:
    """
    Factory function för att skapa en APEX-instans.
    """
    config = config or APEXConfig()

    generators = [generator_factory() for _ in range(config.parallel_generators)]
    generator_pool = DiverseGeneratorPool(generators)

    direct = DirectPattern(generators[0])

    patterns: dict[PatternType, Pattern[T]] = {
        PatternType.DIRECT: direct,
    }

    routes: list[Route] = [
        Route(
            name="simple_direct",
            triggers=["quick", "trivial", "low risk"],
            pattern=PatternType.DIRECT,
        ),
    ]
    router = SemanticRouter(routes=routes)

    return APEXExecutor(
        router=router,
        patterns=patterns,
        quality_fn=quality_fn,
        output_schema=output_schema,
        config=config,
        domain=domain,
    )
