---
phase: 03-data-comparison-engine
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/comparison/data.py
autonomous: true
requirements:
  - DATA-COMP-01
  - DATA-COMP-02
  - DATA-COMP-03
  - DATA-COMP-04
  - DATA-COMP-05

must_haves:
  truths:
    - "DataComparator class implements compare() method"
    - "Full compare mode iterates all rows"
    - "Hash mode computes MD5 checksums"
    - "Sample mode uses primary key interval sampling"
    - "NULL = NULL treated as equal"
    - "BLOB/CLOB/TEXT compared by length only"
  artifacts:
    - path: backend/app/comparison/data.py
      provides: Data comparison engine
      contains: "class DataComparator", "compare()", "_full_compare()", "_hash_verify()", "_sample_compare()"
  key_links:
    - from: backend/app/comparison/data.py
      to: backend/app/adapters/__init__.py
      via: "Uses get_adapter factory"
      pattern: "from app.adapters import get_adapter"
---

<objective>
Implement core DataComparator engine with multiple comparison modes (full, hash, sample).

Purpose: Provide flexible data comparison capabilities based on table size and performance requirements.
Output: DataComparator class with automatic mode selection and batch processing support.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03-data-comparison-engine/CONTEXT.md
@backend/app/adapters/base.py
@backend/app/adapters/mysql.py
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create DataComparator base class with mode selection</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (Comparison Strategy section)
    - backend/app/comparison/schema.py (existing comparator pattern)
    - backend/app/adapters/base.py (adapter interface)
  </read_first>
  <action>
    Create backend/app/comparison/data.py with DataComparator class:

    1. Define dataclasses for comparison results:
       - DataDiffResult: summary + sample differences
       - RowDiff: single row difference with field-level details
       - FieldDiff: single field difference (name, source_value, target_value)

    2. Create DataComparator class with __init__:
       - source_adapter: DatabaseAdapter
       - target_adapter: DatabaseAdapter
       - threshold: int = 100000 (configurable row threshold)
       - batch_size: int = 1000 (rows per batch)
       - sample_size: int = 1000 (rows to sample for large tables)

    3. Implement compare() main entry method:
       - Parameters: source_table, target_table, mode='auto'
       - Get row counts from both tables
       - Mode selection logic:
         - 'full': always use _full_compare()
         - 'hash': always use _hash_verify()
         - 'sample': always use _sample_compare()
         - 'auto': select based on row count vs threshold
       - Return DataDiffResult with summary
  </action>
  <acceptance_criteria>
    - backend/app/comparison/data.py exists
    - File contains "class DataComparator"
    - File contains dataclasses: DataDiffResult, RowDiff, FieldDiff
    - compare() method accepts mode parameter ('auto', 'full', 'hash', 'sample')
    - Mode selection logic uses threshold for 'auto' mode
    - Row counts fetched from both tables
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class (DataComparator|DataDiffResult|RowDiff|FieldDiff)" backend/app/comparison/data.py</automated>
  </verify>
  <done>DataComparator base class created with mode selection logic</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Implement full compare mode for small tables</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - backend/app/comparison/data.py (Task 1 output)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (NULL handling, special fields)
  </read_first>
  <action>
    Implement _full_compare() method in DataComparator:

    1. Fetch all rows from both tables using batched queries:
       - Use LIMIT/OFFSET pagination with batch_size
       - Fetch primary key values first for ordering
       - Use server-side cursor for memory efficiency

    2. Compare rows batch by batch:
       - Build lookup dict from target rows by primary key
       - For each source row:
         - Find matching target row by PK
         - If no match → mark as removed
         - If found → compare field by field
         - If extra target rows → mark as added

    3. Field comparison logic (_compare_field method):
       - Handle NULL values: NULL = NULL → equal
       - Handle BLOB/CLOB/TEXT: compare LENGTH() only
       - Handle normal types: direct value comparison
       - Track field differences in FieldDiff list

    4. Build DataDiffResult:
       - summary: source_row_count, target_row_count, diff_count
       - diffs: list of RowDiff objects
       - has_more: False (full compare returns all)
  </action>
  <acceptance_criteria>
    - _full_compare() method exists
    - Uses batched queries with LIMIT/OFFSET
    - NULL = NULL treated as equal
    - BLOB/CLOB/TEXT compared by length only
    - Returns all row differences
    - Memory-efficient streaming processing
  </acceptance_criteria>
  <verify>
    <automated>grep -A 5 "_full_compare" backend/app/comparison/data.py | head -10</automated>
  </verify>
  <done>Full compare mode implemented with batch processing</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Implement hash verify mode for large tables</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - backend/app/comparison/data.py (Task 1-2 output)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (Hash strategy)
  </read_first>
  <action>
    Implement _hash_verify() method in DataComparator:

    1. Compute MD5 checksum for source table:
       - Build deterministic string representation for each row
       - Order by primary key for consistency
       - Concatenate all rows: "pk1|col1|col2;pk2|col1|col2;..."
       - Handle NULL: use empty string or special marker
       - Handle BLOB/CLOB: use LENGTH() in string
       - Compute MD5 hash of entire string

    2. Compute MD5 checksum for target table (same process)

    3. Compare checksums:
       - If hashes match → return success (tables identical)
       - If hashes differ → tables have differences

    4. Return DataDiffResult:
       - summary: includes hash values for both tables
       - diffs: empty (hash only tells IF different, not WHAT)
       - Note: caller can follow up with _sample_compare() to locate diffs
  </action>
  <acceptance_criteria>
    - _hash_verify() method exists
    - Computes MD5 for source and target tables
    - Row string representation is deterministic
    - NULL handling consistent in hash computation
    - BLOB/CLOB uses LENGTH() in hash
    - Returns hash values in result summary
  </acceptance_criteria>
  <verify>
    <automated>grep -A 5 "_hash_verify" backend/app/comparison/data.py | head -10</automated>
  </verify>
  <done>Hash verify mode implemented for quick difference detection</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Implement sample compare mode for difference localization</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - backend/app/comparison/data.py (Task 1-3 output)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (Sampling strategy)
  </read_first>
  <action>
    Implement _sample_compare() method in DataComparator:

    1. Get primary key column name:
       - From adapter.get_table_metadata()
       - Use first column of primary_key

    2. Calculate sampling interval:
       - interval = total_rows / sample_size
       - Ensure interval >= 1

    3. Build sampling query:
       - SELECT * FROM table WHERE pk_column % interval = 0
       - Or use OFFSET with interval for databases without modulo
       - Limit to sample_size rows

    4. Compare sampled rows:
       - Build lookup dict from sampled target rows
       - Compare each sampled source row with target
       - Use same field comparison as _full_compare()

    5. Return DataDiffResult:
       - summary: sampled_row_count, diff_count, diff_percentage
       - diffs: list of RowDiff from sample
       - has_more: True (implies more differences may exist)
  </action>
  <acceptance_criteria>
    - _sample_compare() method exists
    - Uses primary key interval sampling
    - Sample size configurable (default 1,000)
    - Returns sampled differences
    - has_more=True indicates more differences may exist
    - Sampling query efficient on large tables
  </acceptance_criteria>
  <verify>
    <automated>grep -A 5 "_sample_compare" backend/app/comparison/data.py | head -10</automated>
  </verify>
  <done>Sample compare mode implemented for locating differences in large tables</done>
</task>

</tasks>

<verification>
- DataComparator can be instantiated with adapters
- Full compare returns all differences for small tables
- Hash compare detects differences via MD5 checksum
- Sample compare identifies差异 rows in large tables
- NULL = NULL treated as equal in all modes
- BLOB/CLOB fields compared by length only
- Batch processing handles tables larger than memory
</verification>

<success_criteria>
- backend/app/comparison/data.py contains complete DataComparator
- All comparison modes work correctly
- Memory usage stays bounded during comparison
- Performance acceptable for tables up to 10M rows
</success_criteria>

<output>
After completion, create `.planning/phases/03-data-comparison-engine/03-data-comparison-engine-01-SUMMARY.md` with:
- DataComparator implementation details
- Comparison algorithms used
- NULL handling implementation
- Special field handling approach
</output>
