# Quotation data and arithmetic

The bundled checker supports VND amounts. Use non-negative integer VND values and decimal quantity strings with a dot, not formatted money strings. Apply locale formatting only when displaying values. Keep billable `quantity` distinct from `dimensions_mm` and count each item once even if it appears on multiple pages.

```json
{
  "currency": "VND",
  "tax_mode": "included",
  "vat_rate": "0",
  "discount_vnd": 0,
  "groups": [{"id": "living", "name": "Living room", "subtotal_vnd": 39640000}],
  "items": [
    {"id": "01", "group_id": "living", "name": "Curved sofa", "unit": "linear m", "quantity": "3.8", "unit_price_vnd": 8800000, "amount_vnd": 33440000, "dimensions_mm": [3800], "source": "Hypothetical demonstration brief"},
    {"id": "02", "group_id": "living", "name": "Coffee table", "unit": "piece", "quantity": "1", "unit_price_vnd": 6200000, "amount_vnd": 6200000, "source": "Hypothetical demonstration brief"}
  ],
  "subtotal_vnd": 39640000,
  "vat_vnd": 0,
  "total_vnd": 39640000
}
```

- `included`: unit prices already contain VAT; **do not add VAT again**. `vat_vnd: 0` represents zero **additional** tax, not zero tax inside the price. Record any requested breakdown of included tax separately with an approved calculation basis.
- `excluded`: add `vat_rate` after subtracting the overall discount. The rate is a fraction such as `0.08` and must come from confirmed input.
- `none`: no added tax for this calculation.
- Round each line amount and added tax to one VND with Decimal `ROUND_HALF_UP`. If the source uses another approved policy, adapt the calculation and document the difference before using it.
- Apply `discount_vnd` once to the overall subtotal before added tax. Do not also subtract the same discount at item level.
- Store expected display values in `amount_vnd`, each group's `subtotal_vnd`, and the top-level subtotal/tax/total fields so the checker can reconcile them. Each group must contain at least one item.
- Record the authority for each item in `source`. Add a prose `quantity_basis` for rounded or scale-measured quantities. Never derive construction dimensions from a concept image.

```bash
python3 scripts/check_quote.py project/quote.json \
  --output project/qa/quote-report.json
```

The checker leaves its input unchanged and exits with code 1 for invalid data or mismatched arithmetic. Its report contains calculated values for HTML authoring. It does not validate market rates, tax law, or contract terms. Compare the final HTML/PDF values against this report.

For other currencies, explicitly adapt the schema, precision, rounding rules, and checker before use; the bundled VND validator must not be presented as supporting them.
