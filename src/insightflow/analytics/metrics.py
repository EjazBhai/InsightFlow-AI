METRIC_DEFINITIONS = {
    "gross_sales": "Sum of positive quantity × unit price. Returns are excluded.",
    "net_sales": "Sum of all quantity × unit price, including negative return/cancellation lines.",
    "average_order_value": "Net sales divided by distinct invoice numbers; not a profit measure.",
    "revenue": "Quantity multiplied by unit price. The source has no product costs or margins.",
}


def metric_definition(name: str) -> str | None:
    return METRIC_DEFINITIONS.get(name)
