
import pytest

from insightflow.security import SQLSafetyError, validate_readonly_sql


def test_select_is_limited():
    sql = validate_readonly_sql("SELECT revenue FROM transactions", 10)
    assert "LIMIT 10" in sql.upper()


def test_existing_limit_within_maximum_is_preserved():
    sql = validate_readonly_sql(
        "SELECT revenue FROM transactions LIMIT 5",
        10,
    )
    assert "LIMIT 5" in sql.upper()


def test_limit_above_maximum_is_clamped():
    sql = validate_readonly_sql(
        "SELECT revenue FROM transactions LIMIT 1000",
        10,
    )
    assert "LIMIT 10" in sql.upper()


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE transactions",
        "DELETE FROM transactions",
        "UPDATE transactions SET revenue = 0",
        "INSERT INTO transactions VALUES (1)",
        "SELECT * FROM secrets",
        "SELECT password FROM transactions",
        "SELECT * FROM read_csv('C:/private.csv')",
        "SELECT * FROM read_parquet('C:/private.parquet')",
        "SELECT * FROM transactions; DELETE FROM transactions",
        "ATTACH 'C:/private.db' AS private_db",
        "PRAGMA database_list",
    ],
)
def test_unsafe_sql_rejected(sql: str):
    with pytest.raises(SQLSafetyError):
        validate_readonly_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT revenue FROM transactions LIMIT ALL",
        "SELECT revenue FROM transactions LIMIT (SELECT 1)",
        "SELECT revenue FROM transactions LIMIT unknown_value",
    ],
)
def test_non_numeric_limit_is_rejected_safely(sql: str):
    with pytest.raises(SQLSafetyError):
        validate_readonly_sql(sql)
