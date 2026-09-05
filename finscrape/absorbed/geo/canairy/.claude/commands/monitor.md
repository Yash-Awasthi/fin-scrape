# Monitor Command - Check Trip-Wire Status

Run the monitoring system and display current trip-wire status:

1. Execute `python src/main.py --check-status`
2. Display current readings for all 6 trip-wires
3. Show any active alerts (green/amber/red status)
4. If any reds detected, explain what "TIGHTEN-UP" actions should be taken
5. Generate a summary report in markdown format

Check the logs for any errors and suggest fixes if monitoring failed.

Arguments: $ARGUMENTS (optional: --detailed for full technical report)
