
# InfoStream

`infostream` is a library and executable designed to close the gap between high-level and low-level data manipulation,
or at the very least warn high-level data engineers when their decisions will cause analysis to be excessively slow or produce highly skewed results.

In addition to the technical capabilities, `infostream` tries not to care about where data resides, and contains
a number of data sharing, publishing, and query capabilities which try to give a single machine access
to a global supply of data for any domain participating in `infostream` data sharing.


# Data Retention Goals

 - Use a high-performance, shardable backend such as Postgres to store data
 - Accept any shape of data...
    - transparently widening tables for new keys
    - but also build the client to warn/throw on similar, typo-style mistakes such as `Height` and `height` to prevent avoidable messiness.
 - Support views/dynamic values generated at query-time
    - These sorts of capabilities are available in DB backends, we should let domains where this is useful take advantage of them (I envision GIS organization will heavily rely on these)
 - Node support for the following types of data:
    - Dictionary of string -> any Leaf value or any Node type
    - List of any Leaf value or any Node type
 - Leaf support for the following data values:
    - utf-8 strings
    - 64-bit signed integer
    - double precision float


# Data Retention Non-Goals

 - Support for things like GIS primitives
    - Store your lines as a list of points and write your queries on lists of points
    - Same with polygons, etc. The initial extra work will quickly pay for itself in performance + data provenance.
 - 32, 16, 8 bit numbers - We will assume the database backend can efficiently store small values and avoid the headache of over-specifying type data
 - Any non-utf-8 string encoding. Removing the possibility of having to re-encode a ton of strings in the future helps keep data clean and fast.

# Data Access Goals

 - Similar API as web browser, use a URL format to make requesting data trivially repeatable (and therefore shareable - just send someone a link!)
    - `is://`
 - 





