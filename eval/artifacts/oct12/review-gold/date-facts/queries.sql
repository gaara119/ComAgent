-- invoice_available_dates
SELECT COUNT(*) AS invoice_count, MIN(invoice_date) AS first_invoice_date, MAX(invoice_date) AS last_invoice_date, COUNT(*) FILTER (WHERE invoice_date IS NULL) AS null_invoice_date_count FROM public.invoice;

-- invoice_yearly_summary
SELECT EXTRACT(YEAR FROM invoice_date)::integer AS invoice_year, COUNT(*) AS invoice_count, SUM(total) AS invoice_amount FROM public.invoice GROUP BY EXTRACT(YEAR FROM invoice_date)::integer ORDER BY invoice_year;
