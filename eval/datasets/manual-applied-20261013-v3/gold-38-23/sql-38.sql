-- sql-38 / manual-applied-20261013-v3
-- 找出文件大小已记录的曲目中，字节数最大的前3首，返回曲目编号、名称和字节数；按字节数降序，并列按曲目编号升序。
-- This is the preserved formal reference SQL, not an automatically executed script.
SELECT track_id, name, bytes FROM public.track WHERE bytes IS NOT NULL ORDER BY bytes DESC, track_id ASC LIMIT 3;
