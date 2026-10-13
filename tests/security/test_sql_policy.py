import pytest

from insightflow.security import SQLSafetyError, validate_readonly_sql


def test_select_is_limited():
    assert "LIMIT 10" in validate_readonly_sql("SELECT revenue FROM transactions", 10).upper()


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE transactions",
        "DELETE FROM transactions",
        "SELECT * FROM secrets",
        "SELECT * FROM read_csv('C:/private.csv')",
        "SELECT * FROM transactions; DELETE FROM transactions",
    ],
)
def test_unsafe_sql_rejected(sql: str):
    with pytest.raises(SQLSafetyError):
        validate_readonly_sql(sql)
