source(file.path(ROOT, "scripts", "utils", "models.R"))
output <- file.path(ROOT, "results", "markers")
counts <- read.csv(file.path(output, "quarterly_markers.csv"))
markers <- c("em", "en_numeric", "en_nonnumeric", "curly_apostrophe",
             "curly_quote", "semicolon", "degree_sign", "times_sign", "greek_alpha")
reference_year <- read.csv(file.path(ROOT, "results", "time_series", "breakpoint.csv"))$psi
stopifnot(length(reference_year) == 1, is.finite(reference_year))
reference_index <- (reference_year - STUDY_START_YEAR) * 4
series_set <- lapply(markers, function(marker) load_marker_series(counts, marker))
names(series_set) <- markers
fits <- lapply(series_set, function(s) run_its(s, estimated_breakpoint = reference_index, quiet = TRUE))
models <- lapply(fits, function(f) f$model)
n <- nrow(series_set$em)
k <- length(coef(models$em))
lag <- floor(4 * (n / 100)^(2 / 9))
for (marker in markers) {
  stopifnot(identical(series_set[[marker]]$label, series_set$em$label),
            identical(series_set[[marker]]$n_abstracts, series_set$em$n_abstracts))
}
influence <- sapply(models, function(model) (estfun(model) %*% bread(model))[, "U1.time"] / n)
covariance <- crossprod(influence)
for (ell in seq_len(lag)) {
  gamma <- crossprod(influence[(ell + 1):n, , drop = FALSE], influence[1:(n - ell), , drop = FALSE])
  covariance <- covariance + (1 - ell / (lag + 1)) * (gamma + t(gamma))
}
covariance <- covariance * n / (n - k)
expected <- sapply(models, function(model) newey_west_vcov(model)["U1.time", "U1.time"])
stopifnot(max(abs(diag(covariance) - expected)) < 1e-12,
          min(eigen(covariance, symmetric = TRUE)$values) > -1e-12)
beta <- sapply(models, function(model) coef(model)[["U1.time"]])
before <- sapply(models, function(model) coef(model)[["time"]])
se <- sqrt(diag(covariance))
slopes <- data.frame(marker = markers, endpoint = "2026Q1", quarters = n,
                     breakpoint_year = reference_year, slope_before = before,
                     slope_after = before + beta, slope_change = beta, standard_error = se,
                     slope_change_OR = exp(beta), ci_low = exp(beta - 1.96 * se),
                     ci_high = exp(beta + 1.96 * se),
                     p_slope_change = 2 * pnorm(abs(beta / se), lower.tail = FALSE), row.names = NULL)
slopes$p_holm <- NA_real_
slopes$p_holm[-1] <- p.adjust(slopes$p_slope_change[-1], method = "holm")
write.csv(slopes, file.path(output, "slope_changes.csv"), row.names = FALSE)
contrasts <- do.call(rbind, lapply(markers[-1], function(marker) {
  delta <- beta[["em"]] - beta[[marker]]
  se <- sqrt(covariance["em", "em"] + covariance[marker, marker] - 2 * covariance["em", marker])
  data.frame(comparison_marker = marker, difference_log_odds_per_quarter = delta,
             paired_HAC_standard_error = se, difference_ci_low = delta - 1.96 * se,
             difference_ci_high = delta + 1.96 * se,
             ratio_of_slope_change_ORs = exp(delta), ratio_ci_low = exp(delta - 1.96 * se),
             ratio_ci_high = exp(delta + 1.96 * se), z = delta / se,
             p_value = 2 * pnorm(abs(delta / se), lower.tail = FALSE))
}))
contrasts$p_holm <- p.adjust(contrasts$p_value, method = "holm")
write.csv(contrasts, file.path(output, "slope_comparisons.csv"), row.names = FALSE)
write.csv(data.frame(marker = rownames(covariance), covariance), file.path(output, "joint_covariance.csv"), row.names = FALSE)

searches <- list()
endpoint_fits <- list()
for (endpoint in c("2026Q1", "2026Q2")) {
  estimates <- list()
  samples <- list()
  for (marker in markers) {
    d <- counts[counts$marker == marker, ]
    d <- d[sprintf("%dQ%d", d$year, d$quarter) <= endpoint, ]
    d$n_hits <- d$n_with_marker
    s <- build_series(d, dropped = list())
    set.seed(20260916 + match(marker, markers))
    e <- estimate_breakpoint(s)
    if (is.null(e)) stop("Marker breakpoint fit failed: ", marker)
    estimates[[marker]] <- e
    samples[[marker]] <- s
    searches[[length(searches) + 1]] <- data.frame(
      marker, endpoint, n_quarters = nrow(s), n_abstracts = sum(s$n_abstracts),
      breakpoint_year = index_to_decimal(e$breakpoint),
      ci_low = index_to_decimal(e$ci_low), ci_high = index_to_decimal(e$ci_high), p_break = e$p_break)
  }
  for (marker in markers) {
    f <- run_its(samples[[marker]], estimated_breakpoint = estimates$em$breakpoint, quiet = TRUE)
    tab <- f$summary$odds_ratios
    endpoint_fits[[length(endpoint_fits) + 1]] <- data.frame(
      marker, endpoint, em_breakpoint_year = index_to_decimal(estimates$em$breakpoint), tab)
  }
}
searches <- do.call(rbind, searches)
searches$p_holm <- NA_real_
endpoint_fits <- do.call(rbind, endpoint_fits)
endpoint_fits$p_holm <- NA_real_
for (endpoint in unique(searches$endpoint)) {
  i <- searches$endpoint == endpoint & searches$marker != "em"
  searches$p_holm[i] <- p.adjust(searches$p_break[i], method = "holm")
  for (term in unique(endpoint_fits$term)) {
    i <- endpoint_fits$endpoint == endpoint & endpoint_fits$marker != "em" & endpoint_fits$term == term
    endpoint_fits$p_holm[i] <- p.adjust(endpoint_fits$p_value[i], method = "holm")
  }
}
write.csv(searches, file.path(output, "breakpoint_searches.csv"), row.names = FALSE)
write.csv(endpoint_fits, file.path(output, "endpoint_sensitivity.csv"), row.names = FALSE)
