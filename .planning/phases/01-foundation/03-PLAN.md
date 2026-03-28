---
phase: 01-foundation
plan: 03
type: execute
wave: 1
depends_on: ["02-PLAN"]
files_modified:
  - backend/app/comparison/schema.py
  - backend/app/schemas/api.py
autonomous: true
requirements:
  - SCHEMA-01
  - SCHEMA-02
user_setup: []

must_haves:
  truths:
    - "SchemaComparator can compare two table metadata structures"
    - "Column differences are correctly identified (added, removed, modified)"
    - "Index differences are correctly identified"
  artifacts:
    - path: backend/app/comparison/schema.py
      provides: Schema comparison engine
      contains: "class SchemaComparator", "compare"
  key_links:
    - from: backend/app/comparison/schema.py
      to: backend/app/adapters/mysql.py
      via: "Uses TableMetadata from adapter"
      pattern: "TableMetadata"
---

<objective>
Implement schema comparison engine for comparing table structures.

Purpose: Core business logic for identifying schema differences between tables.
Output: SchemaComparator with column, index, and constraint comparison.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md (D-4: Schema Comparison Algorithm, D-5: Diff Data Structure)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Implement column comparison logic</name>
  <files>backend/app/comparison/schema.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-CONTEXT.md (D-4: Schema Comparison Algorithm)
    - .planning/phases/01-foundation/1-CONTEXT.md (D-5: Diff Data Structure)
  </read_first>
  <action>
    Create backend/app/comparison/schema.py with SchemaComparator:

    1. Define data classes for diff results:
       ```python
       @dataclass
       class ColumnDiff:
           column_name: str
           diff_type: str  # 'added', 'removed', 'modified'
           source_def: dict | None
           target_def: dict | None
           differences: list[str]
       ```

    2. Implement compare_columns() method:
       - Build column maps by name for source and target
       - Find added columns (in target, not in source)
       - Find removed columns (in source, not in target)
       - Find common columns and compare definitions:
         - Compare data type (normalized)
         - Compare nullable
         - Compare default value
         - Compare comment
       - Return list of ColumnDiff

    3. Implement type normalization:
       - Lowercase type names
       - Handle VARCHAR(n) vs VARCHAR(m) as same type with different length
       - Handle DECIMAL(p,s) variations
  </action>
  <acceptance_criteria>
    - backend/app/comparison/schema.py exists
    - File contains "class SchemaComparator"
    - File contains ColumnDiff dataclass
    - compare_columns() identifies added columns
    - compare_columns() identifies removed columns
    - compare_columns() identifies modified columns with specific differences
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class SchemaComparator|class ColumnDiff|def compare_columns" backend/app/comparison/schema.py</automated>
  </verify>
  <done>Column comparison logic implemented and tested</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Implement index comparison logic</name>
  <files>backend/app/comparison/schema.py</files>
  <read_first>
    - backend/app/comparison/schema.py (created in Task 1)
  </read_first>
  <action>
    Extend SchemaComparator with index comparison:

    1. Define IndexDiff dataclass:
       ```python
       @dataclass
       class IndexDiff:
           index_name: str
           diff_type: str  # 'added', 'removed', 'modified'
           source_def: dict | None
           target_def: dict | None
           differences: list[str]
       ```

    2. Implement compare_indexes() method:
       - Build index maps by name
       - Find added indexes
       - Find removed indexes
       - Find common indexes and compare:
         - Compare column list (order matters)
         - Compare unique flag
         - Compare index type (BTREE, HASH, etc.)
       - Return list of IndexDiff
  </action>
  <acceptance_criteria>
    - SchemaComparator has compare_indexes() method
    - IndexDiff dataclass defined
    - compare_indexes() identifies index differences correctly
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class IndexDiff|def compare_indexes" backend/app/comparison/schema.py</automated>
  </verify>
  <done>Index comparison logic implemented</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Implement constraint comparison and main compare method</name>
  <files>backend/app/comparison/schema.py</files>
  <read_first>
    - backend/app/comparison/schema.py (created in Task 1, 2)
  </read_first>
  <action>
    Complete SchemaComparator with constraint comparison and main method:

    1. Define ConstraintDiff dataclass:
       ```python
       @dataclass
       class ConstraintDiff:
           constraint_name: str
           diff_type: str  # 'added', 'removed', 'modified'
           constraint_type: str  # 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE'
           source_def: dict | None
           target_def: dict | None
       ```

    2. Implement compare_constraints() method:
       - Compare primary keys
       - Compare foreign keys (by name or by columns)
       - Compare unique constraints
       - Return list of ConstraintDiff

    3. Implement main compare() method:
       ```python
       def compare(self, source_metadata: dict, target_metadata: dict) -> SchemaDiff:
           return SchemaDiff(
               source_table=source_metadata['table_name'],
               target_table=target_metadata['table_name'],
               column_diffs=self.compare_columns(...),
               index_diffs=self.compare_indexes(...),
               constraint_diffs=self.compare_constraints(...),
           )
       ```

    4. Define SchemaDiff dataclass:
       ```python
       @dataclass
       class SchemaDiff:
           source_table: str
           target_table: str
           column_diffs: list[ColumnDiff]
           index_diffs: list[IndexDiff]
           constraint_diffs: list[ConstraintDiff]
       ```
  </action>
  <acceptance_criteria>
    - SchemaComparator has compare_constraints() method
    - SchemaComparator has compare() main method
    - ConstraintDiff dataclass defined
    - SchemaDiff dataclass defined with all diff types
    - compare() returns complete SchemaDiff
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class ConstraintDiff|class SchemaDiff|def compare\(" backend/app/comparison/schema.py</automated>
  </verify>
  <done>SchemaComparator complete with all comparison methods</done>
</task>

</tasks>

<verification>
- SchemaComparator can compare two table metadata structures
- Column differences correctly identified for all scenarios
- Index differences correctly identified
- Constraint differences correctly identified
- SchemaDiff can be serialized to JSON for API response
</verification>

<success_criteria>
- backend/app/comparison/schema.py contains complete SchemaComparator
- All comparison methods return correct results
- Unit tests pass for various comparison scenarios
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-03-SUMMARY.md` with:
- Comparison algorithm details
- Edge cases handled
- Test results
</output>
