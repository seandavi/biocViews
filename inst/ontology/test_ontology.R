#!/usr/bin/env Rscript
# Test and validate biocViewsVocab.obo file

# Parse OBO file
parse_obo <- function(filename) {
  lines <- readLines(filename)
  
  # Parse header
  header <- list()
  terms <- list()
  current_term <- NULL
  
  for (line in lines) {
    line <- trimws(line)
    
    # Skip empty lines
    if (nchar(line) == 0) {
      if (!is.null(current_term)) {
        terms[[length(terms) + 1]] <- current_term
        current_term <- NULL
      }
      next
    }
    
    # Parse header (before first [Term])
    if (is.null(current_term) && !grepl("^\\[Term\\]", line)) {
      if (grepl(":", line)) {
        parts <- strsplit(line, ":", fixed = TRUE)[[1]]
        if (length(parts) >= 2) {
          key <- trimws(parts[1])
          value <- trimws(paste(parts[-1], collapse = ":"))
          header[[key]] <- value
        }
      }
      next
    }
    
    # Start new term
    if (grepl("^\\[Term\\]", line)) {
      if (!is.null(current_term)) {
        terms[[length(terms) + 1]] <- current_term
      }
      current_term <- list(id = NA, name = NA, def = NA, is_a = character())
      next
    }
    
    # Parse term fields
    if (!is.null(current_term)) {
      if (grepl("^id:", line)) {
        current_term$id <- sub("^id:\\s*", "", line)
      } else if (grepl("^name:", line)) {
        current_term$name <- sub("^name:\\s*", "", line)
      } else if (grepl("^def:", line)) {
        current_term$def <- sub("^def:\\s*", "", line)
      } else if (grepl("^is_a:", line)) {
        # Extract parent ID and name
        is_a_line <- sub("^is_a:\\s*", "", line)
        parent_id <- sub("\\s*!.*$", "", is_a_line)
        current_term$is_a <- c(current_term$is_a, trimws(parent_id))
      }
    }
  }
  
  # Add last term
  if (!is.null(current_term)) {
    terms[[length(terms) + 1]] <- current_term
  }
  
  list(header = header, terms = terms)
}

# Validate OBO structure
validate_obo <- function(obo_data) {
  errors <- character()
  warnings <- character()
  
  # Check header
  cat("Validating header...\n")
  required_header_fields <- c("format-version", "ontology")
  for (field in required_header_fields) {
    if (!(field %in% names(obo_data$header))) {
      errors <- c(errors, paste("Missing required header field:", field))
    }
  }
  
  # Check terms
  cat("Validating terms...\n")
  all_ids <- sapply(obo_data$terms, function(t) t$id)
  
  for (i in seq_along(obo_data$terms)) {
    term <- obo_data$terms[[i]]
    
    # Check required fields
    if (is.na(term$id) || nchar(term$id) == 0) {
      errors <- c(errors, paste("Term", i, "missing id"))
    }
    if (is.na(term$name) || nchar(term$name) == 0) {
      errors <- c(errors, paste("Term", term$id, "missing name"))
    }
    
    # Check ID format
    if (!is.na(term$id) && !grepl("^BIOCVIEWS:\\d{7}$", term$id)) {
      warnings <- c(warnings, paste("Term", term$id, "has non-standard ID format"))
    }
    
    # Check is_a relationships reference valid IDs
    for (parent_id in term$is_a) {
      if (!(parent_id %in% all_ids)) {
        errors <- c(errors, paste("Term", term$id, "references non-existent parent:", parent_id))
      }
    }
  }
  
  list(errors = errors, warnings = warnings)
}

# Check for cycles (DAG validation)
check_cycles <- function(obo_data) {
  cat("Checking for cycles in the ontology...\n")
  
  # Build adjacency list (child -> parents)
  adjacency <- list()
  term_names <- list()
  
  for (term in obo_data$terms) {
    adjacency[[term$id]] <- term$is_a
    term_names[[term$id]] <- term$name
  }
  
  # DFS to detect cycles
  visited <- list()
  rec_stack <- list()
  
  has_cycle <- FALSE
  cycle_path <- NULL
  
  dfs <- function(node, path = character()) {
    if (has_cycle) return()
    
    if (!is.null(rec_stack[[node]]) && rec_stack[[node]]) {
      has_cycle <<- TRUE
      cycle_path <<- c(path, node)
      return()
    }
    
    if (!is.null(visited[[node]]) && visited[[node]]) {
      return()
    }
    
    visited[[node]] <<- TRUE
    rec_stack[[node]] <<- TRUE
    
    if (!is.null(adjacency[[node]])) {
      for (parent in adjacency[[node]]) {
        dfs(parent, c(path, node))
      }
    }
    
    rec_stack[[node]] <<- FALSE
  }
  
  # Check all nodes
  for (node in names(adjacency)) {
    if (is.null(visited[[node]]) || !visited[[node]]) {
      dfs(node)
    }
  }
  
  if (has_cycle) {
    cat("ERROR: Cycle detected in ontology!\n")
    cat("Cycle path:", paste(cycle_path, collapse = " -> "), "\n")
    return(FALSE)
  } else {
    cat("No cycles detected - ontology is a valid DAG\n")
    return(TRUE)
  }
}

# Print summary statistics
print_summary <- function(obo_data) {
  cat("\n=== OBO File Summary ===\n")
  cat("Format version:", obo_data$header[["format-version"]], "\n")
  cat("Ontology:", obo_data$header[["ontology"]], "\n")
  cat("Total terms:", length(obo_data$terms), "\n")
  
  # Count terms with definitions
  terms_with_def <- sum(sapply(obo_data$terms, function(t) !is.na(t$def) && nchar(t$def) > 0))
  cat("Terms with definitions:", terms_with_def, "/", length(obo_data$terms), "\n")
  
  # Count relationships
  total_relationships <- sum(sapply(obo_data$terms, function(t) length(t$is_a)))
  cat("Total is_a relationships:", total_relationships, "\n")
  
  # Find root terms (no parents)
  root_terms <- Filter(function(t) length(t$is_a) == 0, obo_data$terms)
  cat("Root terms:", length(root_terms), "\n")
  for (term in root_terms) {
    cat("  -", term$name, "(", term$id, ")\n")
  }
  
  # Find leaf terms (no children)
  all_parents <- unique(unlist(lapply(obo_data$terms, function(t) t$is_a)))
  all_ids <- sapply(obo_data$terms, function(t) t$id)
  leaf_ids <- setdiff(all_ids, all_parents)
  cat("Leaf terms:", length(leaf_ids), "\n")
  
  # Calculate depth distribution
  depths <- calculate_depths(obo_data)
  max_depth <- max(depths, na.rm = TRUE)
  cat("Maximum depth:", max_depth, "\n")
}

# Calculate depth of each term from root
calculate_depths <- function(obo_data) {
  depths <- list()
  
  # Build child -> parent map
  parents_map <- list()
  for (term in obo_data$terms) {
    parents_map[[term$id]] <- term$is_a
  }
  
  # BFS from root(s)
  queue <- list()
  for (term in obo_data$terms) {
    if (length(term$is_a) == 0) {
      depths[[term$id]] <- 0
      queue <- c(queue, list(term$id))
    }
  }
  
  while (length(queue) > 0) {
    current <- queue[[1]]
    queue <- queue[-1]
    current_depth <- depths[[current]]
    
    # Find children
    for (term in obo_data$terms) {
      if (current %in% term$is_a) {
        if (is.null(depths[[term$id]]) || depths[[term$id]] > current_depth + 1) {
          depths[[term$id]] <- current_depth + 1
          queue <- c(queue, list(term$id))
        }
      }
    }
  }
  
  unlist(depths)
}

# Main execution
main <- function() {
  obo_file <- "biocViewsVocab.obo"
  
  cat("Testing OBO file:", obo_file, "\n\n")
  
  if (!file.exists(obo_file)) {
    stop("OBO file not found: ", obo_file)
  }
  
  # Parse OBO file
  cat("Parsing OBO file...\n")
  obo_data <- parse_obo(obo_file)
  cat("Parsed", length(obo_data$terms), "terms\n\n")
  
  # Validate structure
  validation <- validate_obo(obo_data)
  
  if (length(validation$errors) > 0) {
    cat("\n=== ERRORS ===\n")
    for (error in validation$errors) {
      cat("ERROR:", error, "\n")
    }
  }
  
  if (length(validation$warnings) > 0) {
    cat("\n=== WARNINGS ===\n")
    for (warning in validation$warnings) {
      cat("WARNING:", warning, "\n")
    }
  }
  
  if (length(validation$errors) == 0 && length(validation$warnings) == 0) {
    cat("All validation checks passed!\n\n")
  }
  
  # Check for cycles
  is_dag <- check_cycles(obo_data)
  
  # Print summary
  print_summary(obo_data)
  
  # Return status
  if (length(validation$errors) > 0 || !is_dag) {
    cat("\n=== VALIDATION FAILED ===\n")
    quit(status = 1)
  } else {
    cat("\n=== VALIDATION SUCCESSFUL ===\n")
    quit(status = 0)
  }
}

# Run main function
main()
