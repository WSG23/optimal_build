"""Evaluation engine for declarative rule packs."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


ComparisonResult = Tuple[bool, Dict[str, Any]]


class RuleEngine:
    """Evaluate declarative rule packs against geometry payloads."""

    def validate(
        self,
        rules: Sequence[Mapping[str, Any]],
        geometries: Mapping[str, Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Validate the supplied geometries against the rule definitions."""

        evaluations: List[Dict[str, Any]] = []
        for rule in rules:
            evaluations.append(self._evaluate_rule(rule, geometries))
        return {
            "valid": all(result["passed"] for result in evaluations),
            "results": evaluations,
        }

    def _evaluate_rule(
        self,
        rule: Mapping[str, Any],
        geometries: Mapping[str, Mapping[str, Any]],
    ) -> Dict[str, Any]:
        rule_id = str(rule.get("id") or rule.get("name") or "rule")
        predicate = rule.get("predicate")
        applies_to = rule.get("applies_to")
        title = rule.get("title")
        description = rule.get("description")
        citations = self._normalise_citations(rule.get("citations"))

        target_ids: List[str]
        if isinstance(applies_to, str):
            target_ids = [applies_to]
        elif isinstance(applies_to, Iterable):
            target_ids = [str(item) for item in applies_to]
        else:
            target_ids = list(str(key) for key in geometries.keys())

        evaluations: List[Dict[str, Any]] = []
        offending: List[str] = []

        for geometry_id in target_ids:
            properties = geometries.get(geometry_id)
            if properties is None:
                trace = {
                    "type": "missing_geometry",
                    "result": False,
                    "details": {
                        "geometry_id": geometry_id,
                        "message": "Geometry properties not provided.",
                    },
                }
                evaluations.append(
                    {"geometry_id": geometry_id, "passed": False, "trace": trace}
                )
                offending.append(geometry_id)
                continue

            if not isinstance(properties, Mapping):
                trace = {
                    "type": "invalid_geometry",
                    "result": False,
                    "details": {
                        "geometry_id": geometry_id,
                        "message": "Geometry payload must be a mapping of attributes.",
                    },
                }
                evaluations.append(
                    {"geometry_id": geometry_id, "passed": False, "trace": trace}
                )
                offending.append(geometry_id)
                continue

            result, trace = self._evaluate_predicate(predicate, properties)
            evaluations.append(
                {"geometry_id": geometry_id, "passed": result, "trace": trace}
            )
            if not result:
                offending.append(geometry_id)

        return {
            "rule_id": rule_id,
            "title": title,
            "description": description,
            "passed": not offending,
            "citations": citations,
            "offending_geometry_ids": offending,
            "evaluations": evaluations,
        }

    def _evaluate_predicate(
        self,
        predicate: Any,
        properties: Mapping[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        if predicate is None:
            return True, {
                "type": "noop",
                "result": True,
                "details": {"message": "No predicate supplied."},
                "children": [],
            }

        if isinstance(predicate, Mapping):
            if "all" in predicate:
                return self._evaluate_logical("all", predicate["all"], properties)
            if "any" in predicate:
                return self._evaluate_logical("any", predicate["any"], properties)
            if "not" in predicate:
                result, trace = self._evaluate_predicate(predicate["not"], properties)
                return (not result, self._wrap_trace("not", not result, [trace]))
            if "property" in predicate:
                return self._evaluate_property(predicate, properties)

        if isinstance(predicate, Iterable) and not isinstance(predicate, (str, bytes)):
            return self._evaluate_logical("all", predicate, properties)

        return False, {
            "type": "unsupported_predicate",
            "result": False,
            "details": {"predicate": predicate},
            "children": [],
        }

    def _evaluate_logical(
        self,
        operator: str,
        clauses: Iterable[Any],
        properties: Mapping[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        traces: List[Dict[str, Any]] = []
        results: List[bool] = []
        for clause in clauses:
            result, trace = self._evaluate_predicate(clause, properties)
            traces.append(trace)
            results.append(result)
        if operator == "all":
            outcome = all(results) if results else True
        elif operator == "any":
            outcome = any(results) if results else False
        else:
            outcome = False
        return outcome, self._wrap_trace(operator, outcome, traces)

    def _evaluate_property(
        self,
        predicate: Mapping[str, Any],
        properties: Mapping[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        property_path = predicate.get("property")
        actual = self._extract_value(properties, property_path)
        trace: Dict[str, Any] = {
            "type": "comparison",
            "property": property_path,
            "children": [],
        }
        if actual is None:
            trace.update(
                {
                    "result": False,
                    "details": {
                        "reason": "missing_property",
                        "property": property_path,
                    },
                }
            )
            return False, trace

        if "between" in predicate:
            result, details = self._evaluate_between(actual, predicate["between"])
            trace.update(details)
            return result, trace

        if "in" in predicate:
            result = actual in set(self._as_iterable(predicate["in"]))
            trace.update(
                {
                    "result": result,
                    "details": {
                        "operator": "in",
                        "expected": list(self._as_iterable(predicate["in"]))
                        if predicate.get("in") is not None
                        else [],
                        "actual": actual,
                    },
                }
            )
            return result, trace

        operator = predicate.get("operator") or predicate.get("op")
        expected = predicate.get("value")
        if operator is None and "equals" in predicate:
            operator = "=="
            expected = predicate.get("equals")

        result, details = self._apply_operator(operator, actual, expected)
        trace.update(details)
        return result, trace

    def _evaluate_between(
        self, actual: Any, spec: Mapping[str, Any] | Any
    ) -> ComparisonResult:
        lower = None
        upper = None
        if isinstance(spec, Mapping):
            lower = spec.get("min")
            upper = spec.get("max")
        elif isinstance(spec, (list, tuple)) and len(spec) == 2:
            lower, upper = spec

        details: Dict[str, Any] = {
            "result": True,
            "details": {
                "operator": "between",
                "actual": actual,
                "minimum": lower,
                "maximum": upper,
            },
        }

        if lower is not None:
            valid, _ = self._apply_operator(
                ">=", actual, lower
            )
            if not valid:
                details["result"] = False
                return False, details
        if upper is not None:
            valid, _ = self._apply_operator("<=", actual, upper)
            if not valid:
                details["result"] = False
                return False, details
        return True, details

    def _apply_operator(
        self, operator: str | None, actual: Any, expected: Any
    ) -> ComparisonResult:
        details: Dict[str, Any] = {
            "details": {
                "operator": operator,
                "expected": expected,
                "actual": actual,
            },
        }
        if operator in {"=", "==", "equals"}:
            result = actual == expected
        elif operator == "!=" or operator == "not_equals":
            result = actual != expected
        elif operator in {"<", "<=", ">", ">="}:
            result = self._compare_numeric(operator, actual, expected)
        else:
            result = False
            details["details"]["reason"] = "unsupported_operator"
        details["result"] = result
        return result, details

    def _compare_numeric(self, operator: str, actual: Any, expected: Any) -> bool:
        actual_number = self._as_number(actual)
        expected_number = self._as_number(expected)
        if actual_number is None or expected_number is None:
            return False
        if operator == "<":
            return actual_number < expected_number
        if operator == "<=":
            return actual_number <= expected_number
        if operator == ">":
            return actual_number > expected_number
        if operator == ">=":
            return actual_number >= expected_number
        return False

    @staticmethod
    def _normalise_citations(raw: Any) -> List[Dict[str, Any]]:
        if not raw:
            return []
        if isinstance(raw, Mapping):
            return [dict(raw)]
        if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            return [dict(item) if isinstance(item, Mapping) else {"text": str(item)} for item in raw]
        return [{"text": str(raw)}]

    @staticmethod
    def _wrap_trace(
        operator: str, result: bool, children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "type": operator,
            "result": result,
            "children": children,
        }

    @staticmethod
    def _extract_value(properties: Mapping[str, Any], path: Any) -> Any:
        if not path:
            return None
        parts = str(path).split(".")
        current: Any = properties
        for part in parts:
            if isinstance(current, Mapping) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _as_number(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _as_iterable(value: Any) -> Iterable[Any]:
        if value is None:
            return []
        if isinstance(value, (str, bytes)):
            return [value]
        if isinstance(value, Iterable):
            return value
        return [value]


__all__ = ["RuleEngine"]
