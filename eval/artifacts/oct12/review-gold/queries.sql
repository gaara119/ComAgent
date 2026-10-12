-- role_and_transaction
SELECT current_user AS role_name, current_setting('transaction_read_only') AS transaction_read_only, current_setting('statement_timeout') AS statement_timeout, current_setting('server_version') AS server_version;

-- track_schema
SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'track' AND column_name IN ('track_id','name','bytes','milliseconds') ORDER BY ordinal_position;

-- track_scope
SELECT COUNT(*) AS track_count, COUNT(bytes) AS bytes_known_count, COUNT(*) FILTER (WHERE bytes IS NULL) AS bytes_null_count, COUNT(milliseconds) AS milliseconds_known_count, COUNT(*) FILTER (WHERE milliseconds IS NULL) AS milliseconds_null_count, SUM(milliseconds::numeric) AS milliseconds_sum, AVG(milliseconds) AS average_milliseconds FROM public.track;

-- sql-38_old
SELECT track_id, name, bytes FROM public.track ORDER BY bytes DESC, track_id ASC LIMIT 3;

-- sql-38_current_pending
SELECT track_id, name, bytes FROM public.track ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;

-- sql-38_recommended
SELECT track_id, name, bytes FROM public.track WHERE bytes IS NOT NULL ORDER BY bytes DESC, track_id ASC LIMIT 3;

-- robust-23_recommended
SELECT AVG(milliseconds) AS average_milliseconds FROM public.track;

-- synthetic_desc_default
SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint), (3, 80::bigint), (4, 80::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC, track_id ASC LIMIT 3;

-- synthetic_desc_nulls_last
SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint), (3, 80::bigint), (4, 80::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;

-- synthetic_fewer_known_nulls_last
SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;

-- synthetic_fewer_known_exclusion
SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint)) AS t(track_id, bytes) WHERE bytes IS NOT NULL ORDER BY bytes DESC, track_id ASC LIMIT 3;

-- synthetic_average_null
SELECT AVG(milliseconds) AS average_milliseconds, COUNT(milliseconds) AS nonnull_denominator FROM (VALUES (100), (300), (NULL::integer)) AS t(milliseconds);

-- synthetic_average_empty
SELECT AVG(milliseconds) AS average_milliseconds FROM (VALUES (100), (300)) AS t(milliseconds) WHERE false;
