#!/usr/bin/env python3
"""Detect and fix misaligned markdown tables and box-drawing diagrams."""

import sys


# ── Markdown tables ──────────────────────────────────────────


def find_tables(lines):
    """Find all table blocks (consecutive lines starting with |)."""
    tables = []
    current_table = []
    for i, line in enumerate(lines):
        if line.startswith('|'):
            current_table.append((i, line))
        else:
            if current_table:
                tables.append(current_table)
                current_table = []
    if current_table:
        tables.append(current_table)
    return tables


def is_table_misaligned(table):
    parsed = [row.split('|') for _, row in table]
    num_cols = len(parsed[0])
    for col in range(num_cols):
        widths = set()
        for cells in parsed:
            if col < len(cells):
                widths.add(len(cells[col]))
        if len(widths) > 1:
            return True
    return False


def align_table(table):
    """Rebuild a table with all columns padded to max width."""
    parsed = []
    for _, row in table:
        cells = row.split('|')
        inner = cells[1:-1]
        stripped = [c.strip() for c in inner]
        parsed.append(stripped)

    num_cols = max(len(r) for r in parsed)

    col_widths = [0] * num_cols
    for i, cells in enumerate(parsed):
        if i == 1:
            continue
        for j, cell in enumerate(cells):
            col_widths[j] = max(col_widths[j], len(cell))

    result = []
    for i, cells in enumerate(parsed):
        if i == 1:
            parts = ['|'] + ['-' * (col_widths[j] + 2) + '|' for j in range(num_cols)]
            result.append(''.join(parts))
        else:
            parts = ['|']
            for j, cell in enumerate(cells):
                parts.append(' ' + cell.ljust(col_widths[j]) + ' |')
            result.append(''.join(parts))
    return result


# ── Box-drawing diagrams ─────────────────────────────────────


def find_boxes(lines):
    """Find box blocks: ┌...┐ through └...┘."""
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '┌' in line and '┐' in line:
            block = [(i, line)]
            j = i + 1
            while j < len(lines):
                l = lines[j]
                if '└' in l and '┘' in l:
                    block.append((j, l))
                    break
                elif l.count('│') >= 2:
                    block.append((j, l))
                elif '├' in l and '┤' in l:
                    block.append((j, l))
                else:
                    break
                j += 1
            if len(block) >= 3 and '└' in block[-1][1]:
                blocks.append(block)
            i = j + 1
        else:
            i += 1
    return blocks


def is_box_misaligned(block):
    """Check if left or right edges of a box don't align."""
    left_cols = set()
    right_cols = set()
    for _, line in block:
        # Left edge
        for c in ('┌', '└', '├'):
            if c in line:
                left_cols.add(line.index(c))
                break
        else:
            if '│' in line:
                left_cols.add(line.index('│'))
        # Right edge
        for c in ('┐', '┘', '┤'):
            pos = line.rfind(c)
            if pos >= 0:
                right_cols.add(pos)
                break
        else:
            if '│' in line:
                right_cols.add(line.rfind('│'))
    return len(left_cols) > 1 or len(right_cols) > 1


def align_box(block):
    """Align a box so all edges line up."""
    first_line = block[0][1]
    left_col = first_line.index('┌')

    # Find max content width (between left and right │)
    max_content = 0
    for _, line in block:
        if '│' in line:
            left = line.index('│')
            right = line.rfind('│')
            if right > left:
                max_content = max(max_content, right - left - 1)

    def norm_prefix(line, char):
        """Build prefix that places char at left_col."""
        pos = line.index(char)
        if pos <= left_col:
            return line[:pos] + ' ' * (left_col - pos)
        return line[:left_col]

    result = []
    for _, line in block:
        if '┌' in line and '┐' in line:
            result.append(norm_prefix(line, '┌') + '┌' + '─' * max_content + '┐')

        elif '└' in line and '┘' in line:
            prefix = norm_prefix(line, '└')
            inner = line[line.index('└') + 1:line.rfind('┘')]
            # Preserve mid-connectors (┬, ┴, ┼) at their absolute column
            connector = None
            for mc in ('┬', '┴', '┼'):
                if mc in inner:
                    connector = mc
                    break
            if connector:
                conn_abs = line.index(connector)
                left_dashes = conn_abs - left_col - 1
                right_dashes = left_col + max_content - conn_abs
                if left_dashes < 0:
                    left_dashes = 0
                if right_dashes < 0:
                    right_dashes = 0
                result.append(prefix + '└' + '─' * left_dashes + connector + '─' * right_dashes + '┘')
            else:
                result.append(prefix + '└' + '─' * max_content + '┘')

        elif '├' in line and '┤' in line:
            prefix = norm_prefix(line, '├')
            inner = line[line.index('├') + 1:line.rfind('┤')]
            connector = None
            for mc in ('┼',):
                if mc in inner:
                    connector = mc
                    break
            if connector:
                conn_abs = line.index(connector)
                left_dashes = conn_abs - left_col - 1
                right_dashes = left_col + max_content - conn_abs
                if left_dashes < 0:
                    left_dashes = 0
                if right_dashes < 0:
                    right_dashes = 0
                result.append(prefix + '├' + '─' * left_dashes + connector + '─' * right_dashes + '┤')
            else:
                result.append(prefix + '├' + '─' * max_content + '┤')

        elif '│' in line:
            left = line.index('│')
            right = line.rfind('│')
            if right > left:
                prefix = norm_prefix(line, '│')
                content = line[left + 1:right]
                pad = max_content - len(content)
                result.append(prefix + '│' + content + ' ' * pad + '│')
            else:
                result.append(line)
        else:
            result.append(line)

    return result


# ── Check / Fix ──────────────────────────────────────────────


def check(filepath):
    """Check mode: report misaligned tables and boxes."""
    with open(filepath) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    tables = find_tables(lines)
    boxes = find_boxes(lines)
    all_ok = True

    for table in tables:
        line_num = table[0][0] + 1
        parsed = [(num + 1, row.split('|')) for num, row in table]
        num_cols = len(parsed[0][1])

        misaligned = False
        for col in range(num_cols):
            widths = {}
            for num, cells in parsed:
                if col < len(cells):
                    w = len(cells[col])
                    if w not in widths:
                        widths[w] = []
                    widths[w].append(num)
            if len(widths) > 1:
                misaligned = True
                all_ok = False
                print(f'  Table line {line_num}: Column {col} MISALIGNED - widths: ', end='')
                for w, lns in sorted(widths.items()):
                    print(f'{w}ch (lines {lns})', end='  ')
                print()

        if not misaligned:
            print(f'  Table line {line_num}: OK')

    for box in boxes:
        line_num = box[0][0] + 1
        if is_box_misaligned(box):
            all_ok = False
            left_cols = {}
            right_cols = {}
            for _, line in box:
                for c in ('┌', '└', '├'):
                    if c in line:
                        pos = line.index(c)
                        left_cols.setdefault(pos, 0)
                        left_cols[pos] += 1
                        break
                else:
                    if '│' in line:
                        pos = line.index('│')
                        left_cols.setdefault(pos, 0)
                        left_cols[pos] += 1
                for c in ('┐', '┘', '┤'):
                    pos = line.rfind(c)
                    if pos >= 0:
                        right_cols.setdefault(pos, 0)
                        right_cols[pos] += 1
                        break
                else:
                    if '│' in line:
                        pos = line.rfind('│')
                        right_cols.setdefault(pos, 0)
                        right_cols[pos] += 1
            details = []
            if len(left_cols) > 1:
                details.append(f'left edges: {dict(left_cols)}')
            if len(right_cols) > 1:
                details.append(f'right edges: {dict(right_cols)}')
            print(f'  Box line {line_num}: MISALIGNED - {", ".join(details)}')
        else:
            print(f'  Box line {line_num}: OK')

    if all_ok:
        print('\nAll tables and boxes aligned.')
    return all_ok


def fix(filepath):
    """Fix mode: align all tables and boxes in-place."""
    with open(filepath) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    tables = find_tables(lines)
    boxes = find_boxes(lines)
    fixed_count = 0

    for table in tables:
        if is_table_misaligned(table):
            fixed = align_table(table)
            for i, (idx, _) in enumerate(table):
                lines[idx] = fixed[i]
            fixed_count += 1
            print(f'  Fixed table at line {table[0][0] + 1}')

    for box in boxes:
        if is_box_misaligned(box):
            fixed = align_box(box)
            for i, (idx, _) in enumerate(box):
                lines[idx] = fixed[i]
            fixed_count += 1
            print(f'  Fixed box at line {box[0][0] + 1}')

    if fixed_count:
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        print(f'\n{fixed_count} item(s) fixed.')
    else:
        print('All tables and boxes already aligned.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: fix-md-tables.py [--check | --fix] <file.md>')
        print('  --check  Report misaligned tables/boxes (default)')
        print('  --fix    Fix misaligned tables/boxes in-place')
        sys.exit(1)

    mode = '--check'
    filepath = sys.argv[-1]
    if sys.argv[1] in ('--check', '--fix'):
        mode = sys.argv[1]

    if mode == '--fix':
        fix(filepath)
    else:
        ok = check(filepath)
        sys.exit(0 if ok else 1)
