import bpy
import locale
from collections import namedtuple
from decimal import Decimal

from .mastro_export_utils import (
    header_granularData,
    get_mass_objects_for_scope,
    get_mass_data_for_scope,
    granularData,
    print_ui,
)

HARDCODED_PRINT_PARAMS = header_granularData

NUMERIC_PRINT_PARAMS = {
    "Number of Storeys",
    "Floor Area",
    "Floor to Floor Height",
    "Perimeter",
    "Wall Area",
}

CALC_ITEMS = (
    ('NONE', "—", "No aggregation"),
    ('SUM', "Sum", "Sum of the values"),
    ('MIN', "Min", "Minimum value"),
    ('MAX', "Max", "Maximum value"),
    ('COUNT', "Count", "Number of rows"),
    ('PERCENT', "%", "Percentage of the grand total"),
)

# A single printed column: its position in the table, the configured
# parameter (mastro_CL_print_set_param), the underlying data field to fetch
# (param.param_name) and whether that field holds numeric data. Columns are
# tracked by index rather than by name so the same field can be added more
# than once (e.g. both as a sum and as a percentage).
_Column = namedtuple("Column", ("index", "param", "field_name", "numeric"))


def scan_custom_param_names(context, scope):
    """Return the sorted set of custom property keys found on MaStro mass/block objects in scope"""
    names = set()
    for obj in get_mass_objects_for_scope(context, scope):
        for key in obj.keys():
            if key.startswith("_RNA_UI"):
                continue
            names.add(key)
    return sorted(names)


def get_param_value(row, name):
    if name in HARDCODED_PRINT_PARAMS:
        return row.get(name, "")
    obj = bpy.data.objects.get(row.get("Object", ""))
    if obj is None:
        return ""
    return obj.get(name, "")


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def is_numeric_column(name, rows):
    if name in NUMERIC_PRINT_PARAMS:
        return True
    if name in HARDCODED_PRINT_PARAMS:
        return False
    found_value = False
    for row in rows:
        value = get_param_value(row, name)
        if value == "":
            continue
        found_value = True
        try:
            float(value)
        except (TypeError, ValueError):
            return False
    return found_value


def _format_locale(value):
    return locale.format_string("%.2f", float(value), grouping=True)


def _format_row(cells, col_widths):
    return "".join(f"{str(cell):<{w}}" for cell, w in zip(cells, col_widths))


def _data_row_cells(columns, row):
    cells = []
    for col in columns:
        value = get_param_value(row, col.field_name)
        if col.numeric:
            value = _format_locale(_to_number(value))
        cells.append(value)
    return cells


def _format_dim_value(value, numeric):
    if numeric:
        return _format_locale(_to_number(value))
    return value


def _aggregate_values(rows, value_columns, grand_sums):
    """Compute the aggregated cell value of each value column for a group of rows,
    according to each column's chosen calc type."""
    result = {}
    for col in value_columns:
        calc = col.param.calc
        if calc == 'NONE':
            result[col.index] = None
            continue
        numbers = [_to_number(get_param_value(row, col.field_name)) for row in rows]
        if calc == 'SUM':
            result[col.index] = sum(numbers)
        elif calc == 'MIN':
            result[col.index] = min(numbers) if numbers else 0.0
        elif calc == 'MAX':
            result[col.index] = max(numbers) if numbers else 0.0
        elif calc == 'COUNT':
            result[col.index] = len({row.get("Object", "") for row in rows})
        elif calc == 'PERCENT':
            grand_sum = grand_sums.get(col.index, 0.0)
            result[col.index] = (sum(numbers) / grand_sum * 100.0) if grand_sum else 0.0
    return result


def _format_value_cell(calc, value):
    if value is None:
        return ""
    if calc == 'COUNT':
        return str(int(value))
    if calc == 'PERCENT':
        return f"{_format_locale(value)}%"
    return _format_locale(value)


def _combine_contributions(value_columns, contributions):
    """Combine the per-row aggregate contributions of a group into a single
    subtotal/grand-total aggregate, reusing the values already computed for
    each printed row rather than re-scanning the raw data."""
    result = {}
    for col in value_columns:
        calc = col.param.calc
        numbers = [c[col.index] for c in contributions if c.get(col.index) is not None]
        if calc == 'NONE':
            result[col.index] = None
        elif calc == 'MIN':
            result[col.index] = min(numbers) if numbers else 0.0
        elif calc == 'MAX':
            result[col.index] = max(numbers) if numbers else 0.0
        else:  # SUM, COUNT, PERCENT
            result[col.index] = sum(numbers) if numbers else 0.0
    return result


_BLANK_LINE = object()
_SEPARATOR_LINE = object()


def _subtotal_row_cells(columns, dim_col, dim_value, instance_count, aggs):
    if instance_count is not None:
        dim_value = f"{dim_value} ({instance_count})"
    cells = []
    for col in columns:
        if col.index == dim_col.index:
            value = f"{dim_value} total"
        elif col.index in aggs:
            value = _format_value_cell(col.param.calc, aggs.get(col.index))
        else:
            value = ""
        cells.append(value)
    return cells


def _grouped_row_cells(columns, group_context, group_context_counts, rows, aggs):
    cells = []
    for col in columns:
        if col.index in aggs:
            value = _format_value_cell(col.param.calc, aggs.get(col.index))
        elif col.index in group_context:
            value = _format_dim_value(group_context[col.index], col.numeric)
            if col.index in group_context_counts:
                value = f"{value} ({group_context_counts[col.index]})"
        else:
            value = _format_dim_value(get_param_value(rows[0], col.field_name), col.numeric) if rows else ""
        cells.append(value)
    return cells


def _total_row_cells(columns, aggs):
    cells = []
    for position, col in enumerate(columns):
        if position == 0:
            value = "GRAND TOTAL"
        elif col.index in aggs:
            value = _format_value_cell(col.param.calc, aggs.get(col.index))
        else:
            value = ""
        cells.append(value)
    return cells


def _print_group(rows, dims, columns, value_columns, grand_sums, group_context=None, group_context_counts=None, level=0):
    """Recursively walks the dims, returning (contributions, lines):
    - contributions: one aggregate dict per printed line, reusable by the
      parent level to compute its own subtotal/total without rescanning rows
    - lines: the cell-rows to print, in order, including subtotal rows
    """
    group_context = group_context or {}
    group_context_counts = group_context_counts or {}

    if level == len(dims):
        if group_context:
            aggs = _aggregate_values(rows, value_columns, grand_sums)
            return [aggs], [_grouped_row_cells(columns, group_context, group_context_counts, rows, aggs)]
        else:
            contributions = []
            lines = []
            for row in rows:
                lines.append(_data_row_cells(columns, row))
                contributions.append(_aggregate_values([row], value_columns, grand_sums))
            return contributions, lines

    dim = dims[level]

    groups = []
    for row in rows:
        key = get_param_value(row, dim.field_name)
        if groups and groups[-1][0] == key:
            groups[-1][1].append(row)
        else:
            groups.append((key, [row]))

    all_contributions = []
    lines = []
    for key, group_rows in groups:
        instance_count = None
        if dim.param.calc == 'COUNT':
            instance_count = len({row.get("Object", "") for row in group_rows})

        if dim.param.group:
            new_context = dict(group_context)
            new_context[dim.index] = key
            new_counts = dict(group_context_counts)
            if instance_count is not None:
                new_counts[dim.index] = instance_count
            contributions, sub_lines = _print_group(group_rows, dims, columns, value_columns, grand_sums, new_context, new_counts, level + 1)
        else:
            contributions, sub_lines = _print_group(group_rows, dims, columns, value_columns, grand_sums, group_context, group_context_counts, level + 1)
        if dim.param.total:
            subtotal = _combine_contributions(value_columns, contributions)
            dim_value = _format_dim_value(key, dim.numeric)
            sub_lines.append(_SEPARATOR_LINE)
            sub_lines.append(_subtotal_row_cells(columns, dim, dim_value, instance_count, subtotal))
            sub_lines.append(_BLANK_LINE)
        lines.extend(sub_lines)
        all_contributions.extend(contributions)

    return all_contributions, lines


def build_print_table(context, set_name, set_params, scope):
    if not set_params:
        print_ui("Print set has no columns")
        return

    roughData = get_mass_data_for_scope(context, scope)
    if not roughData:
        print_ui("No data to print")
        return

    rows = granularData(roughData)

    field_names = [param.param_name for param in set_params]
    numeric_flags = [is_numeric_column(field_name, rows) for field_name in field_names]
    columns = [
        _Column(i, param, field_names[i], numeric_flags[i])
        for i, param in enumerate(set_params)
    ]
    names = [param.name for param in set_params]

    # a numeric column is only treated as an aggregated "value" column if it
    # isn't also used as a grouping dimension
    value_columns = [col for col in columns if col.numeric and not col.param.group]
    value_indices = {col.index for col in value_columns}
    dims = [col for col in columns if col.index not in value_indices]

    for dim in reversed(dims):
        if dim.numeric:
            key = lambda row, dim=dim: _to_number(get_param_value(row, dim.field_name))
        else:
            key = lambda row, dim=dim: str(get_param_value(row, dim.field_name))
        rows = sorted(rows, key=key, reverse=(dim.param.sort_order == 'DESC'))

    grand_sums = {
        col.index: sum(_to_number(get_param_value(row, col.field_name)) for row in rows)
        for col in value_columns
    }

    old_locale = locale.getlocale(locale.LC_NUMERIC)
    locale.setlocale(locale.LC_NUMERIC, '')
    try:
        contributions, lines = _print_group(rows, dims, columns, value_columns, grand_sums)
        grand_total = _combine_contributions(value_columns, contributions)
        total_cells = _total_row_cells(columns, grand_total)

        cell_lines = [line for line in lines if isinstance(line, list)]
        col_widths = [
            max(len(str(line[i])) for line in [names] + cell_lines + [total_cells]) + 3
            for i in range(len(names))
        ]

        header_string = _format_row(names, col_widths)
        print_ui("\n")
        print_ui(set_name)
        print_ui(header_string)
        print_ui("-" * len(header_string))

        for line in lines:
            if line is _BLANK_LINE:
                print_ui("")
            elif line is _SEPARATOR_LINE:
                print_ui("-" * len(header_string))
            else:
                print_ui(_format_row(line, col_widths))

        if not lines or lines[-1] is not _BLANK_LINE:
            print_ui("")
        print_ui("=" * len(header_string))
        print_ui(_format_row(total_cells, col_widths))
        print_ui("")
    finally:
        locale.setlocale(locale.LC_NUMERIC, old_locale)
