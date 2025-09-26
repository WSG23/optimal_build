# Singapore BCA fetcher

The SG BCA integration downloads circulars from the Building and Construction Authority's dataset that is published through the [`data.gov.sg` CKAN API](https://data.gov.sg/). The live service requires credentials that are issued by the Singapore government to approved consumers.

## Configuration

The fetcher reads its configuration from the following environment variables:

| Variable | Description |
| --- | --- |
| `SG_BCA_DATASTORE_RESOURCE_ID` | **Required.** CKAN resource identifier for the BCA circular dataset. |
| `SG_BCA_BASE_URL` | Optional override for the CKAN endpoint. Defaults to `https://data.gov.sg/api/action/datastore_search`. |
| `SG_BCA_API_KEY` | Optional API key used when the upstream requires authentication. |
| `SG_BCA_API_KEY_HEADER` | Header name to carry the API key. Defaults to `api-key`. |
| `SG_BCA_PAGE_SIZE` | Page size for pagination requests. Defaults to `100`. |
| `SG_BCA_TIMEOUT` | HTTP timeout (seconds). Defaults to `10`. |
| `SG_BCA_MAX_RETRIES` | Number of retry attempts for transient errors. Defaults to `3`. |
| `SG_BCA_BACKOFF_FACTOR` | Exponential backoff base (seconds). Defaults to `0.5`. |
| `SG_BCA_RATE_LIMIT_PER_MINUTE` | Optional throttle for outbound requests. |
| `SG_BCA_USER_AGENT` | Optional override for the User-Agent header. Defaults to `optimal-build/sg-bca-fetcher`. |
| `SG_BCA_DATE_FIELD` | Optional override for the date field in the dataset (defaults to `circular_date`). |
| `SG_BCA_EXTERNAL_ID_FIELD` | Optional override for the external identifier field (defaults to `circular_no`). |

The fetcher will raise a `FetchError` if the `resource_id` is not provided.

## Operational guidance

* **Authentication:** Production deployments normally require a `data.gov.sg` API key. Request one via the Singapore Government Technology Agency (GovTech) developer portal.
* **Scheduling:** The BCA dataset is typically updated once or twice a week. Running the ingest task twice daily (e.g. 08:00 and 20:00 SGT) keeps the local cache current while staying within rate limits.
* **Monitoring:** The fetcher emits structured log messages with the prefix `sg_bca.fetch`. Ensure your logging pipeline captures warnings and retry events so operators can investigate repeated failures.
