# Search Index Maintenance Report

## Schedule
Search index maintenance is scheduled for Saturday at 02:00 UTC. The operations coordinator reserves a ninety-minute window and posts a status update to the internal service channel before the window begins.

## Scope
The work rebuilds the secondary product index to repair stale category results. The primary index continues serving reads while the secondary index catches up. User accounts and payment data are outside the scope of the rebuild.

## Promotion gate
The promotion gate requires a successful comparison of the product count and the result order for twenty saved queries. If the secondary index differs from the primary by over 0.5% in document count, leave the primary active and investigate.

## Owner and fallback
The search operations team owns the maintenance. If promotion causes an increase in empty results, restore the previous primary alias and record the top three affected queries in the service log.
