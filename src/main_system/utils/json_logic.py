"""
Local JSON Logic evaluator (Python 3.12 compatible).

Why this exists:
- Some upstream `json_logic` PyPI versions historically had Python-3 `dict_keys`
  compatibility issues (e.g., using `dict.keys()[0]`).
- This backend relies on JSON Logic evaluation for eligibility rules; the rule engine
  must be reliable and deterministic across runtimes.

Public API mirrors the upstream library:
    - jsonLogic(logic, data)
"""

from __future__ import annotations

from typing import Any, List, Optional


def _truthy(value: Any) -> bool:
    return bool(value)


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value) if "." in value else float(int(value))
        except ValueError:
            return None
    return None


def _get_var(data: Any, path: Any, default: Any = None) -> Any:
    """
    JSON Logic `var` semantics:
    - var: "" returns current data context
    - var: "a.b.c" traverses dict keys (and list indices if numeric)
    """
    if path is None:
        return default
    if isinstance(path, list):
        # upstream allows ["a.b", default]
        if len(path) == 0:
            return default
        key = path[0]
        default = path[1] if len(path) > 1 else default
        path = key
    if path == "":
        return data
    if not isinstance(path, str):
        return default

    cur = data
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            if part in cur:
                cur = cur[part]
            else:
                return default
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return default
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return default
        else:
            return default
    return cur


def jsonLogic(logic: Any, data: Any = None) -> Any:
    if data is None:
        data = {}

    # primitives
    if logic is None or isinstance(logic, (str, int, float, bool)):
        return logic

    # lists evaluate to list of evaluated items
    if isinstance(logic, list):
        return [jsonLogic(item, data) for item in logic]

    if not isinstance(logic, dict):
        return logic

    if len(logic) != 1:
        raise ValueError("JSON Logic expression must be a single-key dict")

    op, values = next(iter(logic.items()))

    # Normalize values to list for most operators
    if op in ("var",):
        return _get_var(data, values)

    if op == "missing":
        keys = values if isinstance(values, list) else [values]
        missing = []
        for k in keys:
            if isinstance(k, str):
                v = _get_var(data, k, default=None)
                if v is None and (_get_var(data, k, default="__MISSING__") == "__MISSING__"):
                    missing.append(k)
                elif v is None:
                    missing.append(k)
            else:
                missing.append(str(k))
        return missing

    if op == "missing_some":
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError("missing_some expects [min_required, keys]")
        min_required = int(jsonLogic(values[0], data))
        keys = jsonLogic(values[1], data)
        if not isinstance(keys, list):
            raise ValueError("missing_some keys must be list")
        present = 0
        missing = []
        for k in keys:
            if not isinstance(k, str):
                missing.append(str(k))
                continue
            sentinel = object()
            v = _get_var(data, k, default=sentinel)
            if v is sentinel or v is None:
                missing.append(k)
            else:
                present += 1
        if present >= min_required:
            return []
        return missing

    args = values if isinstance(values, list) else [values]

    if op == "!":
        return not _truthy(jsonLogic(args[0], data))
    if op == "!!":
        return _truthy(jsonLogic(args[0], data))

    if op == "and":
        last = None
        for a in args:
            last = jsonLogic(a, data)
            if not _truthy(last):
                return last
        return last

    if op == "or":
        last = None
        for a in args:
            last = jsonLogic(a, data)
            if _truthy(last):
                return last
        return last

    if op in ("==", "==="):
        return jsonLogic(args[0], data) == jsonLogic(args[1], data)
    if op in ("!=", "!=="):
        return jsonLogic(args[0], data) != jsonLogic(args[1], data)

    if op in (">", ">=", "<", "<="):
        left = jsonLogic(args[0], data)
        right = jsonLogic(args[1], data)
        if left is None or right is None:
            return False
        lnum = _to_number(left)
        rnum = _to_number(right)
        if lnum is not None and rnum is not None:
            if op == ">":
                return lnum > rnum
            if op == ">=":
                return lnum >= rnum
            if op == "<":
                return lnum < rnum
            return lnum <= rnum
        try:
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right
            if op == "<":
                return left < right
            return left <= right
        except TypeError:
            return False

    if op == "+":
        total = 0.0
        for a in args:
            n = _to_number(jsonLogic(a, data))
            total += 0.0 if n is None else n
        return total if any(isinstance(jsonLogic(a, data), float) for a in args) else int(total)

    if op == "-":
        if len(args) == 1:
            n = _to_number(jsonLogic(args[0], data)) or 0.0
            return -n
        left = _to_number(jsonLogic(args[0], data)) or 0.0
        right = _to_number(jsonLogic(args[1], data)) or 0.0
        return left - right

    if op == "*":
        prod = 1.0
        for a in args:
            n = _to_number(jsonLogic(a, data)) or 0.0
            prod *= n
        return prod

    if op == "/":
        left = _to_number(jsonLogic(args[0], data)) or 0.0
        right = _to_number(jsonLogic(args[1], data)) or 0.0
        if right == 0:
            raise ZeroDivisionError("division by zero")
        return left / right

    if op == "%":
        left = int(_to_number(jsonLogic(args[0], data)) or 0)
        right = int(_to_number(jsonLogic(args[1], data)) or 0)
        if right == 0:
            raise ZeroDivisionError("modulo by zero")
        return left % right

    if op == "min":
        evaluated = [jsonLogic(a, data) for a in args]
        nums = [x for x in (_to_number(v) for v in evaluated) if x is not None]
        return min(nums) if nums else None

    if op == "max":
        evaluated = [jsonLogic(a, data) for a in args]
        nums = [x for x in (_to_number(v) for v in evaluated) if x is not None]
        return max(nums) if nums else None

    if op == "abs":
        n = _to_number(jsonLogic(args[0], data)) or 0.0
        return abs(n)

    if op == "cat":
        return "".join("" if v is None else str(v) for v in (jsonLogic(a, data) for a in args))

    if op == "substr":
        s = jsonLogic(args[0], data)
        s = "" if s is None else str(s)
        start = int(_to_number(jsonLogic(args[1], data)) or 0)
        length = int(_to_number(jsonLogic(args[2], data)) or 0) if len(args) > 2 else None
        if length is None:
            return s[start:]
        if length >= 0:
            return s[start : start + length]
        return s[start:length]

    if op == "in":
        needle = jsonLogic(args[0], data)
        haystack = jsonLogic(args[1], data)
        if isinstance(haystack, str):
            return str(needle) in haystack
        if isinstance(haystack, list):
            return needle in haystack
        return False

    if op == "merge":
        merged: List[Any] = []
        for a in args:
            v = jsonLogic(a, data)
            if isinstance(v, list):
                merged.extend(v)
            else:
                merged.append(v)
        return merged

    if op == "if":
        i = 0
        while i + 1 < len(args):
            cond = jsonLogic(args[i], data)
            if _truthy(cond):
                return jsonLogic(args[i + 1], data)
            i += 2
        if i < len(args):
            return jsonLogic(args[i], data)
        return None

    if op in ("map", "filter", "all", "none", "some"):
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError(f"{op} expects [array, rule]")
        arr = jsonLogic(values[0], data)
        rule = values[1]
        if not isinstance(arr, list):
            return [] if op in ("map", "filter") else False
        if op == "map":
            return [jsonLogic(rule, item) for item in arr]
        if op == "filter":
            return [item for item in arr if _truthy(jsonLogic(rule, item))]
        if op == "all":
            return all(_truthy(jsonLogic(rule, item)) for item in arr)
        if op == "none":
            return all(not _truthy(jsonLogic(rule, item)) for item in arr)
        return any(_truthy(jsonLogic(rule, item)) for item in arr)

    if op == "reduce":
        if not isinstance(values, list) or len(values) < 2:
            raise ValueError("reduce expects [array, rule, initial?]")
        arr = jsonLogic(values[0], data)
        rule = values[1]
        initial = jsonLogic(values[2], data) if len(values) > 2 else None
        if not isinstance(arr, list):
            return initial
        acc = initial
        for item in arr:
            ctx = {"current": item, "accumulator": acc}
            acc = jsonLogic(rule, ctx)
        return acc

    if op == "log":
        return jsonLogic(args[0], data) if args else None

    if op == "method":
        if not isinstance(values, list) or len(values) < 2:
            raise ValueError("method expects [object, method_name, ...args]")
        target = jsonLogic(values[0], data)
        method_name = jsonLogic(values[1], data)
        method_args = [jsonLogic(v, data) for v in values[2:]]
        if isinstance(target, str) and isinstance(method_name, str):
            if method_name == "lower":
                return target.lower()
            if method_name == "upper":
                return target.upper()
            if method_name == "strip":
                return target.strip()
            if method_name == "startswith":
                return target.startswith(str(method_args[0])) if method_args else False
            if method_name == "endswith":
                return target.endswith(str(method_args[0])) if method_args else False
            if method_name == "replace":
                if len(method_args) >= 2:
                    return target.replace(str(method_args[0]), str(method_args[1]))
                return target
        raise ValueError(f"Unsupported method operation: {method_name}")

    raise ValueError(f"Unsupported JSON Logic operator: {op}")


__all__ = ["jsonLogic"]

