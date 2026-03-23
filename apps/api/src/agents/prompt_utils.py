from __future__ import annotations


def build_template_field_guide(template_modules: list[dict[str, object]]) -> str:
    lines: list[str] = []

    for module in template_modules:
        if not isinstance(module, dict):
            continue

        module_key = _string_or_fallback(module.get("key"), "unknown_module")
        module_label = _string_or_fallback(module.get("label"), module_key)
        lines.append(f"Module {module_key} ({module_label})")

        raw_fields = module.get("fields")
        fields = raw_fields if isinstance(raw_fields, list) else []
        for field in fields:
            if not isinstance(field, dict):
                continue

            field_key = _string_or_fallback(field.get("key"), "unknown_field")
            field_label = _string_or_fallback(field.get("label"), field_key)
            required = "required" if bool(field.get("required")) else "optional"
            kind = _string_or_fallback(field.get("kind"), "unknown")
            description = _string_or_fallback(field.get("description"), "")

            if kind == "scalar":
                value_type = _string_or_fallback(field.get("value_type"), "string")
                line = (
                    f"- {module_key}.{field_key} | scalar<{value_type}> | {required} | "
                    f"{field_label}"
                )
                if description:
                    line = f"{line} | {description}"
                lines.append(line)
                continue

            min_rows = field.get("min_rows")
            line = f"- {module_key}.{field_key} | table | {required} | {field_label}"
            if isinstance(min_rows, int):
                line = f"{line} | min_rows={min_rows}"
            if description:
                line = f"{line} | {description}"
            lines.append(line)

            raw_columns = field.get("columns")
            columns = raw_columns if isinstance(raw_columns, list) else []
            if columns:
                rendered_columns: list[str] = []
                for column in columns:
                    if not isinstance(column, dict):
                        continue

                    column_key = _string_or_fallback(column.get("key"), "unknown_column")
                    column_type = _string_or_fallback(column.get("value_type"), "string")
                    column_required = "required" if bool(column.get("required")) else "optional"
                    rendered_columns.append(
                        f"{column_key}<{column_type}> {column_required}"
                    )

                if rendered_columns:
                    lines.append(f"  columns: {', '.join(rendered_columns)}")

    if not lines:
        return "- No template fields were provided."

    return "\n".join(lines)


def _string_or_fallback(value: object, fallback: str) -> str:
    if isinstance(value, str):
        normalized = " ".join(value.split()).strip()
        if normalized:
            return normalized
    return fallback
