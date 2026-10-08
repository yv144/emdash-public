source(file.path(ROOT, "scripts", "utils", "models.R"))
output <- file.path(ROOT, "results", "time_series")
save_table <- function(x, name) write.csv(x, file.path(output, name), row.names = FALSE)
set.seed(20260916)

series <- load_em_dash_series()
estimate <- estimate_breakpoint(series)
if (is.null(estimate)) stop("The main breakpoint fit failed.")
fit <- run_its(series, estimated_breakpoint = estimate$breakpoint, quiet = TRUE)
effect <- fit$effect
predictions <- data.frame(
  year = series$year, quarter = series$quarter, decimal_year = series$decimal_year,
  n_abstracts = series$n_abstracts, n_with_em_dash = series$n_hits,
  observed = series$rate, fitted = effect$fitted, counterfactual = effect$expected,
  cf_lo = effect$expected_low, cf_hi = effect$expected_high, post = fit$prepared$post
)
save_table(predictions, "predictions.csv")
last <- nrow(series)
save_table(data.frame(
  psi = index_to_decimal(estimate$breakpoint), psi_lo = index_to_decimal(estimate$ci_low),
  psi_hi = index_to_decimal(estimate$ci_high), p_break = estimate$p_break,
  effect_pp = effect$effect_pp, effect_pct = effect$effect_pct,
  fitted_end = effect$fitted[last], cf_end = effect$expected[last],
  cf_end_lo = effect$expected_low[last], cf_end_hi = effect$expected_high[last],
  end_label = series$label[last], n_quarters = last, n_abstracts = sum(series$n_abstracts)
), "breakpoint.csv")
coefficients <- fit$summary$odds_ratios
save_table(coefficients, "coefficients.csv")
beta <- coef(fit$model)
covariance <- fit$summary$vcov
terms <- c("time", "U1.time")
post_slope <- sum(beta[terms])
post_se <- sqrt(sum(covariance[terms, terms]))
save_table(data.frame(
  slope_before = beta[["time"]], slope_after = post_slope,
  post_break_OR = exp(post_slope), ci_low = exp(post_slope - 1.96 * post_se),
  ci_high = exp(post_slope + 1.96 * post_se),
  p_value = 2 * pnorm(abs(post_slope / post_se), lower.tail = FALSE)
), "post_break_trend.csv")
lb <- Box.test(residuals(fit$model, type = "pearson"),
               lag = min(8, floor(nrow(series) / 4)), type = "Ljung-Box")
save_table(data.frame(dispersion = summary(fit$model)$dispersion,
                     ljung_box_p = lb$p.value, newey_west_lag = 3), "diagnostics.csv")

grid <- expand.grid(start_year = c(2019, 2020),
                    mode = c("estimated", "release", "lagged", "exclude", "double"))
sensitivity <- lapply(seq_len(nrow(grid)), function(i) {
  set.seed(20260916)
  s <- load_em_dash_series(start_year = grid$start_year[i])
  f <- run_its(s, mode = as.character(grid$mode[i]), start_year = grid$start_year[i], quiet = TRUE)
  data.frame(start_year = grid$start_year[i], mode = grid$mode[i],
             n_quarters = nrow(f$prepared),
             breakpoint_year = index_to_decimal(attr(f$prepared, "breakpoint_time")[1], grid$start_year[i]),
             effect_pp = f$effect$effect_pp, effect_pct = f$effect$effect_pct)
})
save_table(do.call(rbind, sensitivity), "sensitivity.csv")

fields <- read.csv(file.path(ROOT, "results", "field_timing", "departures.csv"))$area
field_results <- lapply(fields, function(area) {
  set.seed(20260916)
  s <- load_em_dash_series(area = area)
  e <- estimate_breakpoint(s)
  if (is.null(e)) stop("Field breakpoint fit failed: ", area)
  f <- run_its(s, estimated_breakpoint = e$breakpoint, quiet = TRUE)
  common <- run_its(s, estimated_breakpoint = estimate$breakpoint, quiet = TRUE)
  data.frame(area, breakpoint_year = index_to_decimal(e$breakpoint),
             ci_low = index_to_decimal(e$ci_low), ci_high = index_to_decimal(e$ci_high),
             p_break = e$p_break, pre_trend_OR = exp(coef(f$model)[["time"]]),
             effect_pp = f$effect$effect_pp, effect_at_common_breakpoint_pp = common$effect$effect_pp)
})
write.csv(do.call(rbind, field_results), file.path(ROOT, "results", "field_timing", "breakpoints.csv"), row.names = FALSE)
capture.output(sessionInfo(), file = file.path(output, "session.txt"))
