"""Evaluation engine for geometry rule packs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, Dict, List

from app.core.models.geometry import GeometryEntity, GeometryGraph, Space


@dataclass
class _EvaluationContext:
    """Shared context available during predicate evaluation."""

    graph: GeometryGraph
    rule: Mapping[str, Any]


class RulesEngine:
    """Evaluate rules expressed with a small predicate DSL."""

    def __init__(self, pack: Mapping[str, Any]) -> None:
        self._pack = dict(pack)
        rules = self._pack.get("rules", [])
        if not isinstance(rules, Sequence):
            raise TypeError("Rule pack definition must include a sequence under 'rules'")
        self._rules: List[Mapping[str, Any]] = [dict(rule) for rule in rules]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate(self, graph: GeometryGraph) -> Dict[str, Any]:
        """Evaluate the configured rules against the provided geometry graph."""

        context = _EvaluationContext(graph=graph, rule={})
        results: List[Dict[str, Any]] = []
        total_checked = 0
        total_violations = 0

        for rule in self._rules:
            context.rule = rule
            evaluation = self._evaluate_rule(rule, context)
            results.append(evaluation)
            total_checked += int(evaluation.get("checked", 0))
            total_violations += len(evaluation.get("violations", []))

        summary = {
            "total_rules": len(self._rules),
            "evaluated_rules": len(results),
            "violations": total_violations,
            "checked_entities": total_checked,
        }
        return {"results": results, "summary": summary}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _evaluate_rule(
        self, rule: Mapping[str, Any], context: _EvaluationContext
    ) -> Dict[str, Any]:
        predicate = rule.get("predicate")
        if not isinstance(predicate, Mapping):
            raise ValueError(f"Rule '{rule.get('id')}' missing predicate definition")

        target = str(rule.get("target", "spaces"))
        violations: List[Dict[str, Any]] = []
        checked = 0

        for entity in self._iter_target_entities(context.graph, target):
            where_clause = rule.get("where")
            if isinstance(where_clause, Mapping):
                matches, _, _ = self._evaluate_predicate(where_clause, entity, context)
                if not matches:
                    continue
            checked += 1

            passed, messages, facts = self._evaluate_predicate(predicate, entity, context)
            if not passed:
                violation = {
                    "entity_id": str(getattr(entity, "id", "")),
                    "messages": messages or [f"Rule '{rule.get('id')}' was not satisfied"],
                    "facts": facts,
                    "attributes": self._build_violation_attributes(entity, target),
                }
                violations.append(violation)

        return {
            "rule_id": str(rule.get("id", "")),
            "title": rule.get("title"),
            "target": target,
            "citation": rule.get("citation"),
            "passed": not violations,
            "checked": checked,
            "violations": violations,
        }

    def _iter_target_entities(
        self, graph: GeometryGraph, target: str
    ) -> Iterable[GeometryEntity]:
        key = target.lower()
        if key in {"space", "spaces"}:
            return list(graph.spaces.values())
        if key in {"level", "levels"}:
            return list(graph.levels.values())
        if key in {"wall", "walls"}:
            return list(graph.walls.values())
        if key in {"door", "doors"}:
            return list(graph.doors.values())
        if key in {"fixture", "fixtures"}:
            return list(graph.fixtures.values())
        raise ValueError(f"Unsupported rule target: {target}")

    def _evaluate_predicate(
        self,
        predicate: Mapping[str, Any],
        entity: GeometryEntity,
        context: _EvaluationContext,
    ) -> tuple[bool, List[str], List[Dict[str, Any]]]:
        if "all" in predicate:
            return self._evaluate_all(predicate["all"], entity, context, predicate.get("message"))
        if "any" in predicate:
            return self._evaluate_any(predicate["any"], entity, context, predicate.get("message"))
        if "not" in predicate:
            return self._evaluate_not(predicate["not"], entity, context, predicate.get("message"))
        if "exists" in predicate:
            field = str(predicate["exists"])
            value = self._resolve_field(entity, field, context)
            if value is not None:
                return True, [], []
            message = predicate.get("message") or f"Expected '{field}' to be present"
            fact = {
                "field": field,
                "operator": "exists",
                "expected": True,
                "actual": value,
            }
            return False, [message], [fact]
        if "field" in predicate:
            return self._evaluate_field_predicate(predicate, entity, context)
        raise ValueError(f"Unsupported predicate structure: {predicate}")

    def _evaluate_all(
        self,
        predicates: Sequence[Mapping[str, Any]],
        entity: GeometryEntity,
        context: _EvaluationContext,
        message: str | None,
    ) -> tuple[bool, List[str], List[Dict[str, Any]]]:
        all_passed = True
        messages: List[str] = []
        facts: List[Dict[str, Any]] = []
        for item in predicates:
            passed, child_messages, child_facts = self._evaluate_predicate(item, entity, context)
            if not passed:
                all_passed = False
                messages.extend(child_messages)
                facts.extend(child_facts)
        if all_passed:
            return True, [], []
        if message:
            messages.insert(0, message)
        return False, messages, facts

    def _evaluate_any(
        self,
        predicates: Sequence[Mapping[str, Any]],
        entity: GeometryEntity,
        context: _EvaluationContext,
        message: str | None,
    ) -> tuple[bool, List[str], List[Dict[str, Any]]]:
        failure_messages: List[str] = []
        failure_facts: List[Dict[str, Any]] = []
        for item in predicates:
            passed, child_messages, child_facts = self._evaluate_predicate(item, entity, context)
            if passed:
                return True, [], []
            failure_messages.extend(child_messages)
            failure_facts.extend(child_facts)
        combined_message = message or "None of the predicate options were satisfied"
        return False, [combined_message, *failure_messages], failure_facts

    def _evaluate_not(
        self,
        predicate: Mapping[str, Any],
        entity: GeometryEntity,
        context: _EvaluationContext,
        message: str | None,
    ) -> tuple[bool, List[str], List[Dict[str, Any]]]:
        passed, child_messages, child_facts = self._evaluate_predicate(predicate, entity, context)
        if passed:
            failure_message = message or "Negated predicate evaluated to true"
            return False, [failure_message, *child_messages], child_facts
        return True, [], []

    def _evaluate_field_predicate(
        self,
        predicate: Mapping[str, Any],
        entity: GeometryEntity,
        context: _EvaluationContext,
    ) -> tuple[bool, List[str], List[Dict[str, Any]]]:
        field = str(predicate.get("field"))
        operator = str(predicate.get("operator", "=="))
        actual = self._resolve_field(entity, field, context)

        if "value_field" in predicate:
            expected = self._resolve_field(entity, str(predicate["value_field"]), context)
        elif "value_path" in predicate:
            expected = self._resolve_field(entity, str(predicate["value_path"]), context)
        else:
            expected = predicate.get("value")
        if isinstance(expected, str) and expected.startswith("$"):
            expected = self._resolve_field(entity, expected[1:], context)

        comparison, normalised_actual, normalised_expected, reason = self._apply_operator(
            operator, actual, expected
        )
        if comparison:
            return True, [], []

        message = predicate.get("message")
        if not message:
            if reason:
                message = reason
            else:
                message = self._format_failure_message(field, operator, normalised_expected, normalised_actual)
        fact: Dict[str, Any] = {
            "field": field,
            "operator": operator,
            "expected": normalised_expected,
            "actual": normalised_actual,
        }
        if reason:
            fact["message"] = reason
        return False, [message], [fact]

    def _apply_operator(
        self, operator: str, actual: Any, expected: Any
    ) -> tuple[bool, Any, Any, str | None]:
        op = operator.lower()
        if op in {">", ">=", "<", "<="}:
            numeric_actual, numeric_expected, comparable = self._coerce_numeric_pair(actual, expected)
            if not comparable:
                reason = f"Cannot compare values using '{operator}': {actual!r} and {expected!r}"
                return False, actual, expected, reason
            actual = numeric_actual
            expected = numeric_expected
        try:
            if op == "==":
                return actual == expected, actual, expected, None
            if op == "!=":
                return actual != expected, actual, expected, None
            if op == ">":
                return bool(actual > expected), actual, expected, None
            if op == ">=":
                return bool(actual >= expected), actual, expected, None
            if op == "<":
                return bool(actual < expected), actual, expected, None
            if op == "<=":
                return bool(actual <= expected), actual, expected, None
            if op == "in":
                container = expected
                if container is None:
                    return False, actual, expected, "Expected a container for 'in' comparison"
                if not isinstance(container, (str, bytes)) and not isinstance(container, Iterable):
                    return False, actual, expected, "Right-hand side of 'in' must be iterable"
                return bool(actual in container), actual, expected, None
            if op == "not_in":
                container = expected
                if container is None:
                    return False, actual, expected, "Expected a container for 'not_in' comparison"
                if not isinstance(container, (str, bytes)) and not isinstance(container, Iterable):
                    return False, actual, expected, "Right-hand side of 'not_in' must be iterable"
                return bool(actual not in container), actual, expected, None
            if op == "contains":
                if actual is None:
                    return False, actual, expected, "Left-hand side of 'contains' is empty"
                if isinstance(actual, Mapping):
                    return bool(expected in actual or expected in actual.values()), actual, expected, None
                if isinstance(actual, (str, bytes)):
                    return bool(str(expected) in actual), actual, expected, None
                if isinstance(actual, Iterable):
                    return bool(expected in actual), actual, expected, None
                return False, actual, expected, "Left-hand side of 'contains' must be iterable"
            if op == "not_contains":
                if actual is None:
                    return True, actual, expected, None
                if isinstance(actual, Mapping):
                    return bool(expected not in actual and expected not in actual.values()), actual, expected, None
                if isinstance(actual, (str, bytes)):
                    return bool(str(expected) not in actual), actual, expected, None
                if isinstance(actual, Iterable):
                    return bool(expected not in actual), actual, expected, None
                return False, actual, expected, "Left-hand side of 'not_contains' must be iterable"
            if op == "is_truthy":
                return bool(actual), actual, expected, None
            if op == "is_falsy":
                return (not bool(actual)), actual, expected, None
        except TypeError as exc:  # pragma: no cover - defensive against edge cases
            return False, actual, expected, str(exc)
        return False, actual, expected, f"Unsupported operator '{operator}'"

    def _coerce_numeric_pair(self, left: Any, right: Any) -> tuple[Any, Any, bool]:
        left_num = self._coerce_numeric(left)
        right_num = self._coerce_numeric(right)
        if left_num is None or right_num is None:
            return left, right, False
        return left_num, right_num, True

    def _coerce_numeric(self, value: Any) -> float | None:
        if isinstance(value, bool):  # Avoid treating booleans as numbers
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _resolve_field(
        self, entity: GeometryEntity, path: str, context: _EvaluationContext
    ) -> Any:
        if not path:
            return None
        segments = path.split(".")
        root: Any
        if segments[0] == "graph":
            root = context.graph
            segments = segments[1:]
        elif segments[0] == "computed":
            return self._resolve_computed(segments[1:], entity, context)
        else:
            root = entity
        value: Any = root
        for segment in segments:
            if value is None:
                return None
            if isinstance(value, Mapping):
                value = value.get(segment)
            else:
                value = getattr(value, segment, None)
        return value

    def _resolve_computed(
        self, segments: Sequence[str], entity: GeometryEntity, context: _EvaluationContext
    ) -> Any:
        if not segments:
            return None
        key = segments[0]
        if key == "area":
            return self._space_area(entity)
        if key == "perimeter":
            return self._space_perimeter(entity)
        if key == "level":
            level_id = getattr(entity, "level_id", None)
            if level_id:
                return context.graph.levels.get(level_id)
            return None
        return None

    def _space_area(self, entity: GeometryEntity) -> float:
        if not isinstance(entity, Space):
            boundary = getattr(entity, "boundary", None)
        else:
            boundary = entity.boundary
        if not boundary:
            return 0.0
        points: List[tuple[float, float]] = []
        for point in boundary:
            if isinstance(point, Sequence) and len(point) >= 2:
                points.append((float(point[0]), float(point[1])))
            elif isinstance(point, Mapping):
                x = point.get("x")
                y = point.get("y")
                if x is None or y is None:
                    continue
                points.append((float(x), float(y)))
        if len(points) < 3:
            return 0.0
        if points[0] != points[-1]:
            points.append(points[0])
        area = 0.0
        for idx in range(len(points) - 1):
            x1, y1 = points[idx]
            x2, y2 = points[idx + 1]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    def _space_perimeter(self, entity: GeometryEntity) -> float:
        if not isinstance(entity, Space):
            boundary = getattr(entity, "boundary", None)
        else:
            boundary = entity.boundary
        if not boundary:
            return 0.0
        points: List[tuple[float, float]] = []
        for point in boundary:
            if isinstance(point, Sequence) and len(point) >= 2:
                points.append((float(point[0]), float(point[1])))
            elif isinstance(point, Mapping):
                x = point.get("x")
                y = point.get("y")
                if x is None or y is None:
                    continue
                points.append((float(x), float(y)))
        if len(points) < 2:
            return 0.0
        perimeter = 0.0
        for idx in range(len(points)):
            x1, y1 = points[idx]
            x2, y2 = points[(idx + 1) % len(points)]
            perimeter += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return perimeter

    def _format_failure_message(
        self, field: str, operator: str, expected: Any, actual: Any
    ) -> str:
        if operator in {"in", "not_in", "contains", "not_contains"}:
            return (
                f"Field '{field}' with value {actual!r} failed condition "
                f"'{operator}' against {expected!r}"
            )
        if operator in {"is_truthy", "is_falsy"}:
            verb = "truthy" if operator == "is_truthy" else "falsy"
            return f"Field '{field}' expected to be {verb} but was {actual!r}"
        return (
            f"Field '{field}' with value {actual!r} does not satisfy "
            f"{operator} {expected!r}"
        )

    def _build_violation_attributes(self, entity: GeometryEntity, target: str) -> Dict[str, Any]:
        attributes: Dict[str, Any] = {"target": target}
        name = getattr(entity, "name", None)
        if name:
            attributes["name"] = name
        level_id = getattr(entity, "level_id", None)
        if level_id:
            attributes["level_id"] = level_id
        metadata = getattr(entity, "metadata", None)
        if isinstance(metadata, MutableMapping) and metadata:
            attributes["metadata"] = dict(metadata)
        return attributes


__all__ = ["RulesEngine"]
