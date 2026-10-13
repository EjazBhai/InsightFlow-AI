from insightflow.security import validate_readonly_sql


def test_select_alias_is_allowed_in_order_by():
    sql = "SELECT country, SUM(revenue) AS net_sales FROM transactions GROUP BY country ORDER BY net_sales DESC"
    assert "ORDER BY net_sales DESC" in validate_readonly_sql(sql)
