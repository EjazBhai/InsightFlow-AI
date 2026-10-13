# SQL safety

SQL is parsed with SQLGlot before execution. The policy accepts one SELECT-like query over `transactions`, checks a table and column allowlist, caps rows, blocks semicolon-separated statements, disallows mutation/DDL, and blocks DuckDB file-read, attach, configuration, and extension terms. Tests cover DDL/DML, arbitrary-table access, file reads, and stacked statements.
