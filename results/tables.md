## Data loading

| Platform                    | Nodes/sec   | Rels/sec   | Total load time   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------------|------------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A         | N/A        | N/A               | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A         | N/A        | N/A               | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A         | N/A        | N/A               | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A         | N/A        | N/A               | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

## Traversals


### traversal_1hop

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

### traversal_2hop

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

### traversal_3hop

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

## Lookups


### point_lookup

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

### indexed_filtered_lookup

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

## Aggregations

| Platform                    | p50   | p95   | Notes                                                                                                                                                                                                                                                         |
|-----------------------------|-------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A   | N/A   | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A   | N/A   | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A   | N/A   | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A   | N/A   | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

## Mixed workload (concurrency sweep)

| Platform                    | Concurrency   | R/W mix   | Throughput   | Latency                                                                                                                                                                                                                                                       |
|-----------------------------|---------------|-----------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CognoDB Cloud (c0 free)     | N/A           | N/A       | N/A          | TransientError: {code: Neo.TransientError.General.OutOfTimeError} {message: context deadline exceeded}                                                                                                                                                        |
| Neo4j Aura Free             | N/A           | N/A       | N/A          | ClientError: {code: Neo.ClientError.Transaction.TransactionHookFailed} {message: You have exceeded the logical size limit of 200000 nodes in your database (attempt to add 2000 nodes would reach 200726 nodes). Please consider upgrading to the next tier.} |
| Memgraph Cloud              | N/A           | N/A       | N/A          | ClientError: {code: Memgraph.ClientError.Security.Unauthenticated} {message: Authentication failure}                                                                                                                                                          |
| ArangoDB Oasis (free trial) | N/A           | N/A       | N/A          | DocumentInsertError: [HTTP 400][ERR 600] VPackError error: Expecting digit                                                                                                                                                                                    |

## Footprint

| Platform   | Node count   | Rel count   | Notes   |
|------------|--------------|-------------|---------|
