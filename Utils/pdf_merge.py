"""Minimal pure-Python PDF merger.

Handles simple PDFs such as those produced by Blender's grease pencil exporter.
Does not support encrypted PDFs or compressed cross-reference streams (PDF 1.5+).
"""

import re


def _read_xref(data):
    """Return (xref dict {obj_id: byte_offset}, trailer_dict_bytes)."""
    # Find startxref
    m = list(re.finditer(rb'startxref\s+(\d+)', data))
    if not m:
        raise ValueError("startxref not found")
    xref_offset = int(m[-1].group(1))

    xref = {}
    pos = xref_offset
    assert data[pos:pos+4] == b'xref', "xref keyword expected"
    pos += 4

    trailer_bytes = b''
    while True:
        # skip whitespace
        while pos < len(data) and data[pos:pos+1] in (b' ', b'\r', b'\n', b'\t'):
            pos += 1
        if data[pos:pos+7] == b'trailer':
            pos += 7
            trailer_bytes = data[pos:]
            break
        # subsection header: first_id count
        line_end = data.index(b'\n', pos)
        parts = data[pos:line_end].split()
        pos = line_end + 1
        first_id = int(parts[0])
        count    = int(parts[1])
        for i in range(count):
            entry = data[pos:pos+20]
            pos += 20
            offset = int(entry[0:10])
            in_use = entry[17:18]
            if in_use == b'n':
                xref[first_id + i] = offset

    return xref, trailer_bytes


def _parse_trailer(trailer_bytes):
    """Return dict with Root and Size from trailer."""
    m = re.search(rb'<<(.+?)>>', trailer_bytes, re.DOTALL)
    if not m:
        raise ValueError("trailer dict not found")
    body = m.group(1)
    root_m = re.search(rb'/Root\s+(\d+)\s+\d+\s+R', body)
    size_m = re.search(rb'/Size\s+(\d+)', body)
    return {
        'root': int(root_m.group(1)) if root_m else None,
        'size': int(size_m.group(1)) if size_m else 0,
    }


def _read_object(data, offset):
    """Read one indirect object from data at offset. Returns raw bytes of object body."""
    # find 'obj' keyword
    start = data.index(b'obj', offset) + 3
    # find matching 'endobj'
    end = data.index(b'endobj', start)
    return data[start:end].strip()


def _collect_pages(data, xref, root_id):
    """Return list of (page_id, page_body_bytes) in order."""
    # Read catalog
    catalog = _read_object(data, xref[root_id])
    pages_m = re.search(rb'/Pages\s+(\d+)\s+\d+\s+R', catalog)
    pages_root_id = int(pages_m.group(1))

    pages = []
    _collect_page_tree(data, xref, pages_root_id, pages)
    return pages


def _collect_page_tree(data, xref, node_id, result):
    body = _read_object(data, xref[node_id])
    type_m = re.search(rb'/Type\s*/(\w+)', body)
    node_type = type_m.group(1) if type_m else b''
    if node_type == b'Pages':
        kids_m = re.search(rb'/Kids\s*\[([^\]]+)\]', body, re.DOTALL)
        if kids_m:
            for kid_m in re.finditer(rb'(\d+)\s+\d+\s+R', kids_m.group(1)):
                _collect_page_tree(data, xref, int(kid_m.group(1)), result)
    else:
        result.append((node_id, body))


def _collect_all_objects(data, xref, root_id):
    """Return {obj_id: raw_body_bytes} for all reachable objects."""
    objects = {}
    _walk_objects(data, xref, root_id, objects)
    return objects


def _walk_objects(data, xref, obj_id, visited):
    if obj_id in visited or obj_id not in xref:
        return
    body = _read_object(data, xref[obj_id])
    visited[obj_id] = body
    for ref_m in re.finditer(rb'(\d+)\s+\d+\s+R', body):
        _walk_objects(data, xref, int(ref_m.group(1)), visited)


def merge(input_paths, output_path):
    """Merge PDF files at input_paths into output_path."""
    # Gather all objects from all PDFs, remapping ids to avoid conflicts.
    # New id space: 1 = catalog, 2 = Pages root, 3..N = per-file objects
    all_objects   = {}  # new_id -> body_bytes (with old refs still in place)
    id_remap      = {}  # (file_index, old_id) -> new_id
    page_new_ids  = []  # new ids of /Page objects in order
    next_id       = 3   # 1 and 2 reserved for catalog and Pages tree

    for fi, path in enumerate(input_paths):
        with open(path, 'rb') as f:
            data = f.read()

        xref, trailer_bytes = _read_xref(data)
        info = _parse_trailer(trailer_bytes)
        root_id = info['root']

        objects = _collect_all_objects(data, xref, root_id)
        pages   = _collect_pages(data, xref, root_id)

        # Assign new ids
        for old_id in objects:
            id_remap[(fi, old_id)] = next_id
            next_id += 1

        # Store objects with (fi, old_id) tag for later ref rewriting
        for old_id, body in objects.items():
            new_id = id_remap[(fi, old_id)]
            all_objects[new_id] = (fi, old_id, body)

        for (old_page_id, _) in pages:
            page_new_ids.append(id_remap[(fi, old_page_id)])

    # Rewrite all object references
    def rewrite_refs(fi, body):
        def replacer(m):
            old_ref_id = int(m.group(1))
            gen        = m.group(2)
            key        = (fi, old_ref_id)
            if key in id_remap:
                return f'{id_remap[key]} {gen} R'.encode()
            return m.group(0)
        return re.sub(rb'(\d+)\s+(\d+)\s+R', replacer, body)

    # Build output PDF
    out = bytearray()
    out += b'%PDF-1.4\n'

    offsets = {}  # new_id -> byte offset

    # Write all remapped objects (skip /Catalog and /Pages nodes — we rebuild them)
    skip_types = {b'Catalog', b'Pages'}
    for new_id, (fi, old_id, body) in sorted(all_objects.items()):
        type_m = re.search(rb'/Type\s*/(\w+)', body)
        if type_m and type_m.group(1) in skip_types:
            continue
        rewritten = rewrite_refs(fi, body)
        # Patch /Parent references in /Page objects to point to new Pages root (id=2)
        rewritten = re.sub(rb'/Parent\s+\d+\s+\d+\s+R', b'/Parent 2 0 R', rewritten)
        offsets[new_id] = len(out)
        out += f'{new_id} 0 obj\n'.encode()
        out += rewritten + b'\nendobj\n'

    # Write Pages tree (id=2)
    kids = ' '.join(f'{pid} 0 R' for pid in page_new_ids)
    offsets[2] = len(out)
    out += f'2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_new_ids)} >>\nendobj\n'.encode()

    # Write Catalog (id=1)
    offsets[1] = len(out)
    out += b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'

    # xref table
    xref_offset = len(out)
    all_ids = sorted(offsets.keys())
    max_id  = max(all_ids)
    out += b'xref\n'
    out += f'0 {max_id + 1}\n'.encode()
    out += b'0000000000 65535 f \n'
    for i in range(1, max_id + 1):
        if i in offsets:
            out += f'{offsets[i]:010d} 00000 n \n'.encode()
        else:
            out += b'0000000000 65535 f \n'

    out += b'trailer\n'
    out += f'<< /Size {max_id + 1} /Root 1 0 R >>\n'.encode()
    out += b'startxref\n'
    out += f'{xref_offset}\n'.encode()
    out += b'%%EOF\n'

    with open(output_path, 'wb') as f:
        f.write(out)
