# Data dictionary

`transactions` contains invoice number, stock code, description, quantity, invoice date, unit price, optional customer ID, country, `is_cancellation`, and `revenue`. Invoice and stock identifiers are retained as strings. Invalid required IDs/dates/numeric prices are rejected and reported. Exact duplicate lines are dropped; returns are not dropped.
