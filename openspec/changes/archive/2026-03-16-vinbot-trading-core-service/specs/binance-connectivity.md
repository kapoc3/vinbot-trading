## ADDED Requirements

### Requirement: HMAC-SHA256 Authentication
The system SHALL sign all authenticated requests using HMAC-SHA256 with the user's Secret Key as the key and the query string + body as the payload.

#### Scenario: Successful Signature Generation
- **WHEN** a request to a private endpoint is prepared
- **THEN** an `X-MBX-APIKEY` header is added and a `signature` parameter is appended to the query/body.

### Requirement: Server Time Synchronization
The system SHALL synchronize its local timestamp with the Binance server time to avoid "timestamp outside of recvWindow" errors.

#### Scenario: Initial Sinking
- **WHEN** the service starts
- **THEN** it calls `GET /api/v3/time` and calculates the offset for subsequent requests.
