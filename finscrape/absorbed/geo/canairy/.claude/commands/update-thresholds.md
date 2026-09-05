# Update Thresholds Command - Modify Alert Levels

Update trip-wire thresholds based on new research or changed circumstances:

1. Review current thresholds in config/config.yaml
2. Analyze historical data to validate proposed changes
3. Update threshold values with proper justification
4. Test new thresholds against recent data
5. Document changes in logs/threshold-changes.log
6. Notify household members of alert level modifications

Arguments: $ARGUMENTS should specify which trip-wire and new values
Example: `/update-thresholds treasury_tail green:2.5 amber:6.0`
