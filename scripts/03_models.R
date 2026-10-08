script <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE))
ROOT <- dirname(dirname(normalizePath(script)))
source(file.path(ROOT, "scripts", "analysis", "time_series.R"))
source(file.path(ROOT, "scripts", "analysis", "markers.R"))
