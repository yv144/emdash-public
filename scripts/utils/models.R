STUDY_START_YEAR <- 2019

SENSITIVITY_START_YEARS <- c(2019, 2020)

CHATGPT_QUARTER <- c(2022, 4)
RELEASE_DECIMAL <- 2022 + 11 / 12

BREAKPOINT_MODE <- "estimated"

INCLUDE_LEVEL_JUMP <- TRUE

DROPPED_QUARTERS <- list(c(2026, 2))

ADJUST_SEASONALITY <- TRUE

NEWEY_WEST_LAG <- NULL

PREPARED_DIR <- file.path(ROOT, "results", "preparation")
EM_DASH_PATH <- file.path(PREPARED_DIR, "quarterly_em_dash.csv")
MARKERS_PATH <- file.path(ROOT, "results", "markers", "quarterly_markers.csv")

required_packages <- c("dplyr", "segmented", "sandwich", "lmtest")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0) {
  stop("Install first: install.packages(c('",
       paste(missing_packages, collapse = "', '"), "'))")
}

suppressPackageStartupMessages({
  library(dplyr)
  library(segmented)
  library(sandwich)
  library(lmtest)
})

quarter_index <- function(year, quarter, start_year = STUDY_START_YEAR) {
  (year - start_year) * 4 + (quarter - 1)
}

quarter_decimal <- function(year, quarter) year + (quarter - 1) / 4

quarter_label <- function(year, quarter) sprintf("%dQ%d", year, quarter)

index_to_label <- function(index, start_year = STUDY_START_YEAR) {
  sprintf("%dQ%d", start_year + floor(index / 4), floor(index %% 4) + 1)
}

index_to_decimal <- function(index, start_year = STUDY_START_YEAR) {
  start_year + index / 4
}

months_since_release <- function(index, start_year = STUDY_START_YEAR) {
  (index_to_decimal(index, start_year) - RELEASE_DECIMAL) * 12
}

p_value_column <- function(coefficient_table) {
  grep("^Pr\\(", colnames(coefficient_table), value = TRUE)[1]
}

build_series <- function(quarterly_counts, start_year = STUDY_START_YEAR,
                         dropped = DROPPED_QUARTERS) {
  series <- quarterly_counts |>
    filter(year >= start_year) |>
    arrange(year, quarter)

  for (dropped_quarter in dropped) {
    series <- series |>
      filter(!(year == dropped_quarter[1] & quarter == dropped_quarter[2]))
  }

  series |>
    mutate(
      time = quarter_index(year, quarter, start_year),
      decimal_year = quarter_decimal(year, quarter),
      label = quarter_label(year, quarter),
      rate = 100 * n_hits / n_abstracts,
      quarter_factor = factor(quarter)
    )
}

load_em_dash_series <- function(area = NULL, start_year = STUDY_START_YEAR,
                                path = EM_DASH_PATH) {
  if (!file.exists(path)) {
    stop("Cannot find ", path, "\n  Run: python prepare_data.py", call. = FALSE)
  }
  counts <- read.csv(path, stringsAsFactors = FALSE)

  if (!is.null(area)) {
    counts <- counts[counts$area %in% area, , drop = FALSE]
    if (nrow(counts) == 0) stop("No rows for area = ", area)
  }

  counts |>
    group_by(year, quarter) |>
    summarise(n_abstracts = sum(n_abstracts),
              n_hits = sum(n_with_em_dash),
              .groups = "drop") |>
    build_series(start_year = start_year)
}

load_marker_counts <- function(path = MARKERS_PATH) {
  if (!file.exists(path)) {
    stop("Cannot find ", path, "\n  Run: python prepare_data.py", call. = FALSE)
  }
  read.csv(path, stringsAsFactors = FALSE)
}

load_marker_series <- function(marker_counts, marker,
                               start_year = STUDY_START_YEAR) {
  marker_counts[marker_counts$marker == marker, ] |>
    rename(n_hits = n_with_marker) |>
    build_series(start_year = start_year)
}

fit_trend_model <- function(series, seasonality = ADJUST_SEASONALITY,
                            level_jump = FALSE) {
  terms <- "time"
  if (level_jump && "post" %in% names(series) && length(unique(series$post)) > 1) {
    terms <- c(terms, "post")
  }
  if (seasonality && length(unique(series$quarter)) > 1) {
    terms <- c(terms, "quarter_factor")
  }

  formula <- as.formula(paste(
    "cbind(n_hits, n_abstracts - n_hits) ~", paste(terms, collapse = " + ")
  ))

  do.call("glm", list(formula = formula, data = series,
                      family = quasibinomial(link = "logit")))
}

estimate_breakpoint <- function(series, n_breakpoints = 1,
                                seasonality = ADJUST_SEASONALITY) {
  trend_model <- fit_trend_model(series, seasonality, level_jump = FALSE)

  score_test <- try(pscore.test(trend_model, ~time), silent = TRUE)
  segmented_model <- try(
    segmented(trend_model, seg.Z = ~time, npsi = n_breakpoints), silent = TRUE
  )
  if (inherits(segmented_model, "try-error")) return(NULL)

  interval <- confint(segmented_model)
  list(
    model = segmented_model,
    breakpoint = interval[1, 1],
    ci_low = interval[1, 2],
    ci_high = interval[1, 3],
    p_break = if (inherits(score_test, "try-error")) NA_real_ else score_test$p.value,
    segment_slopes = slope(segmented_model)$time
  )
}

prepare_series <- function(series, mode = BREAKPOINT_MODE,
                           estimated_breakpoint = NULL,
                           start_year = STUDY_START_YEAR,
                           chatgpt_quarter = CHATGPT_QUARTER) {
  release_time <- quarter_index(chatgpt_quarter[1], chatgpt_quarter[2], start_year)
  if (max(series$time) < release_time) {
    stop("The series ends before the release quarter.")
  }
  if (is.null(estimated_breakpoint)) {
    stop("prepare_series() needs estimated_breakpoint from estimate_breakpoint().")
  }

  lag_quarters <- max(0, round(estimated_breakpoint - release_time))
  lagged_time <- release_time + lag_quarters

  breakpoint_time <- switch(
    mode,
    estimated = estimated_breakpoint,
    release   = release_time,
    lagged    = lagged_time,
    exclude   = lagged_time,
    double    = c(release_time, lagged_time),
    stop("BREAKPOINT_MODE must be estimated, release, lagged, exclude or double")
  )

  prepared <- series
  n_excluded <- 0L
  if (mode == "exclude") {
    keep <- prepared$time < release_time | prepared$time >= lagged_time
    n_excluded <- sum(!keep)
    prepared <- prepared[keep, , drop = FALSE]
  }

  prepared$post <- as.integer(prepared$time >= breakpoint_time[1])

  attr(prepared, "breakpoint_time") <- breakpoint_time
  attr(prepared, "release_time") <- release_time
  attr(prepared, "lagged_time") <- lagged_time
  attr(prepared, "lag_quarters") <- lag_quarters
  attr(prepared, "mode") <- mode
  attr(prepared, "n_excluded") <- n_excluded
  attr(prepared, "start_year") <- start_year
  prepared
}

fit_at_breakpoint <- function(prepared, seasonality = ADJUST_SEASONALITY,
                              level_jump = INCLUDE_LEVEL_JUMP) {
  trend_model <- fit_trend_model(prepared, seasonality, level_jump)
  segmented(trend_model, seg.Z = ~time, psi = attr(prepared, "breakpoint_time"),
            control = seg.control(it.max = 0))
}

newey_west_vcov <- function(model, lag = NEWEY_WEST_LAG) {
  if (is.null(lag)) lag <- floor(4 * (nobs(model) / 100)^(2 / 9))
  NeweyWest(model, lag = lag, prewhite = FALSE, adjust = TRUE)
}

summarise_model <- function(model, quiet = FALSE) {
  robust_vcov <- newey_west_vcov(model)
  coefficient_table <- coeftest(model, vcov. = robust_vcov)
  p_column <- p_value_column(coefficient_table)

  terms <- intersect(c("time", "post", "U1.time", "U2.time"),
                     rownames(coefficient_table))
  odds_ratios <- data.frame(
    term = terms,
    odds_ratio = exp(coefficient_table[terms, "Estimate"]),
    ci_low = exp(coefficient_table[terms, "Estimate"] -
                   1.96 * coefficient_table[terms, "Std. Error"]),
    ci_high = exp(coefficient_table[terms, "Estimate"] +
                    1.96 * coefficient_table[terms, "Std. Error"]),
    p_value = coefficient_table[terms, p_column],
    row.names = NULL
  )

  if (!quiet) {
    cat("\n--- Coefficients (Newey-West standard errors) ---\n")
    print(coefficient_table)
    cat("\n--- On the odds-ratio scale ---\n")
    print(odds_ratios, digits = 4)
    cat("\n  time     quarterly trend before the breakpoint\n")
    cat("  post     immediate step at the breakpoint\n")
    cat("  U1.time  change in quarterly trend at the breakpoint\n")
    if ("U2.time" %in% terms) {
      cat("  U2.time  further change in trend at the second breakpoint\n")
    }
  }
  invisible(list(coefficients = coefficient_table, odds_ratios = odds_ratios,
                 vcov = robust_vcov))
}

counterfactual_effect <- function(model, prepared, robust_vcov = NULL,
                                  quiet = FALSE) {
  coefficients <- coef(model)
  design <- model.matrix(model)[, names(coefficients), drop = FALSE]

  intervention_terms <- grep("^(U[0-9]+\\.|psi[0-9]+\\.|post$)", colnames(design))
  counterfactual_design <- design
  counterfactual_design[, intervention_terms] <- 0

  inverse_link <- model$family$linkinv
  fitted_pct <- 100 * inverse_link(as.vector(design %*% coefficients))
  expected_pct <- 100 * inverse_link(
    as.vector(counterfactual_design %*% coefficients)
  )

  if (!is.null(robust_vcov)) {
    standard_error <- sqrt(rowSums(
      (counterfactual_design %*% robust_vcov) * counterfactual_design
    ))
    expected_low <- 100 * inverse_link(
      as.vector(counterfactual_design %*% coefficients) - 1.96 * standard_error
    )
    expected_high <- 100 * inverse_link(
      as.vector(counterfactual_design %*% coefficients) + 1.96 * standard_error
    )
  } else {
    expected_low <- expected_high <- rep(NA_real_, nrow(design))
  }

  final <- nrow(prepared)
  effect_pp <- fitted_pct[final] - expected_pct[final]
  effect_pct <- 100 * (fitted_pct[final] / expected_pct[final] - 1)

  if (!quiet) {
    cat("\n--- Effect in the final quarter ---\n")
    cat(sprintf("Quarter:        %s\n", prepared$label[final]))
    cat(sprintf("Fitted:         %.2f%%\n", fitted_pct[final]))
    if (!is.na(expected_low[final])) {
      cat(sprintf("Counterfactual: %.2f%% (95%% CI %.2f to %.2f)\n",
                  expected_pct[final], expected_low[final], expected_high[final]))
    } else {
      cat(sprintf("Counterfactual: %.2f%%\n", expected_pct[final]))
    }
    cat(sprintf("Absolute:       %+.2f percentage points\n", effect_pp))
    cat(sprintf("Relative:       %+.1f%%\n", effect_pct))
  }

  list(fitted = fitted_pct, expected = expected_pct,
       expected_low = expected_low, expected_high = expected_high,
       effect_pp = effect_pp, effect_pct = effect_pct)
}

report_diagnostics <- function(model, prepared) {
  cat("\n--- Diagnostics ---\n")
  cat(sprintf("Observations: %d quarters (%s to %s)\n",
              nrow(prepared), prepared$label[1], prepared$label[nrow(prepared)]))
  cat(sprintf("Dispersion:   %.2f (1.0 = nominal binomial)\n",
              summary(model)$dispersion))

  residuals_pearson <- residuals(model, type = "pearson")
  ljung_box_lag <- min(8, floor(nrow(prepared) / 4))
  if (ljung_box_lag >= 1) {
    ljung_box <- Box.test(residuals_pearson, lag = ljung_box_lag,
                          type = "Ljung-Box")
    cat(sprintf("Ljung-Box (lag %d): X2 = %.2f, p = %.4f%s\n",
                ljung_box_lag, ljung_box$statistic, ljung_box$p.value,
                if (ljung_box$p.value < 0.05) "  <- autocorrelation present" else ""))
  }
}

run_its <- function(series, mode = BREAKPOINT_MODE, estimated_breakpoint = NULL,
                    start_year = STUDY_START_YEAR, quiet = FALSE) {
  if (is.null(estimated_breakpoint)) {
    estimate <- estimate_breakpoint(series)
    if (is.null(estimate)) stop("Breakpoint estimation did not converge.")
    estimated_breakpoint <- estimate$breakpoint
  }

  prepared <- prepare_series(series, mode = mode,
                             estimated_breakpoint = estimated_breakpoint,
                             start_year = start_year)
  model <- fit_at_breakpoint(prepared)

  if (!quiet) {
    cat(sprintf("\n===== ITS: start %d, '%s' breakpoint at %s (%.2f) =====\n",
                start_year, mode,
                index_to_label(attr(prepared, "breakpoint_time")[1], start_year),
                index_to_decimal(attr(prepared, "breakpoint_time")[1], start_year)))
    if (attr(prepared, "n_excluded") > 0) {
      cat(sprintf("Transition quarters excluded: %d\n",
                  attr(prepared, "n_excluded")))
    }
    report_diagnostics(model, prepared)
  }

  summary_tables <- summarise_model(model, quiet = quiet)
  effect <- counterfactual_effect(model, prepared, summary_tables$vcov,
                                  quiet = quiet)

  invisible(list(series = series, prepared = prepared, model = model,
                 summary = summary_tables, effect = effect))
}

baseline_departure <- function(series, baseline_end = c(2022, 4),
                               n_sd = 3, run_length = 2) {
  baseline_rows <- series$year < baseline_end[1] |
    (series$year == baseline_end[1] & series$quarter <= baseline_end[2])
  baseline_rates <- series$rate[baseline_rows]
  if (length(baseline_rates) < 4) return(NULL)

  baseline_mean <- mean(baseline_rates)
  threshold <- baseline_mean + n_sd * stats::sd(baseline_rates)

  above <- series$rate > threshold
  if (length(above) >= run_length) {
    for (i in seq_len(length(above) - run_length + 1)) {
      if (all(above[i:(i + run_length - 1)])) {
        return(list(onset = series$decimal_year[i], label = series$label[i],
                    baseline_pct = baseline_mean, threshold_pct = threshold))
      }
    }
  }
  list(onset = NA_real_, label = NA_character_,
       baseline_pct = baseline_mean, threshold_pct = threshold)
}