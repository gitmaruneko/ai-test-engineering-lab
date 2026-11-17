# Checkout Reliability Incident Review

## Incident summary
The checkout team saw elevated payment authorization errors on July 14 after releasing Checkout Gateway 2.18. The first alert fired at 09:12 UTC. Customers could browse products and fill carts, but a subset could not complete payment. The incident commander declared severity two at 09:19 UTC when the error rate exceeded the published response threshold. The support desk opened a single incident thread and directed merchants to its updates.

## Rollback trigger
The rollback trigger was a payment authorization error rate above 5% for ten consecutive minutes across both gateway pools. The monitoring panel reported 6.2% at 09:24 UTC, and the incident commander authorized rollback at 09:26 UTC. The primary on-call engineer reverted the gateway version rather than changing the payment retry policy during the incident. The rollback was complete at 09:34 UTC.

## Customer impact
The incident affected requests reaching the two regional gateway pools that received the release. Healthy regions continued serving their normal traffic. The billing analyst estimated that approximately 840 checkout attempts failed before mitigation. The estimate counted affected attempts rather than unique shoppers, since some customers retried. The report records no confirmed duplicate authorizations in the reviewed transaction sample.

## Detection and triage
The error-rate alert was linked to a dashboard grouped by gateway version, region, and payment processor. The first responder confirmed the rise using server logs before escalating. Rates for version 2.17 remained close to baseline, and the payment processor reported no concurrent service disruption. The on-call engineer shared those observations with incident command and kept a running timeline so decisions could be reconstructed for this review.

## Root cause
The release included a change to the payment request serializer. A fallback path converted an expired payment token into an empty string before submitting the request. Two payment processors treated the empty string as an explicit malformed credential and rejected authorization. The regression appeared only when a cached token expired while a customer had an active checkout session. The deployment health check used fresh tokens, so it passed.

## Recovery verification
After rollback, the quality engineer ran simulated payments in both affected pools using fresh and expired tokens. A separate observer compared gateway metrics with the prior release baseline. Availability was declared restored at 09:42 UTC after the authorization error rate stayed below 1% for five minutes and the dashboard showed no unexpected increase in retries. Support then updated its incident thread with the recovery time and customer instructions.

## Individual payment inquiries
Support agents should ask for the merchant order reference and the approximate time of the attempt. They can compare those details with the incident window and direct customers who still need help to the billing queue. Staff should use the established case system to handle customer-specific data. This training report contains aggregate figures and operating procedures. It contains no payment credentials or customer identities.

## Why the canary missed it
The canary sent a small percentage of synthetic transactions through one pool during the deployment. Its test accounts generated a new payment token for each attempt, which left the expired-token path uncovered. The observed error signal counted all payment activity together and was diluted by unrelated successful payments. The team plans to separate synthetic success metrics by credential state and to add expired-token checks before widening traffic.

## Remediation ownership
The checkout reliability team owns the serializer fix and the engineering manager tracks delivery in the standard release board. The quality engineering team owns the regression test and the monitoring team owns the new alert view. The checkout product manager coordinates the associated release notes. Each owner should report whether its change is deployed, how it was verified, and when the evidence was added to the shared incident record.

## Follow-up test cases
Regression coverage should include an expired token, a missing token, a valid token, and an authorization retry following a recoverable processor response. The reviewer should verify that requests with expired credentials are rejected locally with an understandable customer response. Requests with a fresh token should follow the normal authorization path exactly once. The test report should include which gateway versions were compared and the observed outcome for each case.

## Communication cadence
During the incident, the support desk posted an initial notice when severity two was declared. The incident commander scheduled updates every fifteen minutes while impact continued. Each update distinguished confirmed observations from actions still in progress. The customer-facing recovery notice went out after post-rollback checks passed. This cadence gave support representatives a reliable place to check status, reducing duplicate investigations and inconsistent explanations.

## Release policy
Changes to payment request encoding must have at least one review from the checkout reliability team. A deployment candidate should be tested against both gateway pools before the rollout expands. The release checklist calls for a named on-call engineer, a tested rollback procedure, and a monitoring link. Approval should record an explicit decision and the evidence reviewed. Operators verify the current release state before running any mitigation procedure.

## Dashboard maintenance
Monitoring staff review the incident dashboard after meaningful gateway changes. Alerts should distinguish request counts from customer counts and clearly show the aggregation window. Per-version plots help a responder see whether an error follows a release rather than the payment processor. The dashboard owner should update links to runbooks when monitoring panels are renamed. Operators record screenshots and metric timestamps in the incident case after significant changes.

## Review outcome
The review identified two gaps in release evidence. Neither synthetic coverage nor the dashboard distinguished expiration-related failures clearly enough to catch the regression early. The next review will compare canary results before and after the new test is introduced. The team will mark its follow-up complete when the test detects the known faulty version, the corrected build passes, and the updated dashboard shows the signal for each gateway pool.
