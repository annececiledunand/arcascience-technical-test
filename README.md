# Biomedical Literature Retrieval Test

## Overview

This recruitment test evaluates your ability to implement and optimize a biomedical literature retrieval system. You'll work with the National Center for Biotechnology Information (NCBI) E-utilities API to retrieve research articles relating hemostatic devices to urology indicators.

## Background

Hemostatic devices are crucial in surgical procedures to control bleeding. Understanding which hemostatic devices are being discussed in conjunction with urological procedures can provide valuable insights for medical research and product development. Your task is to implement a robust and efficient system to retrieve this information from biomedical literature databases.

## Current Implementation

The current code in this repository:
- Defines lists of hemostatic devices and urology indicators in `config.py`
- Has a basic implementation of PMC database searching in `search.py`
- Uses a simple query creation function in `main.py`

**Important note**: For testing purposes, the main script currently uses smaller datasets:
- `HEMOSTATIC_DEVICES_MINI_FLAT` (only 10 devices and their synonyms)
- `UROLOGY_INDICATORS_MINI_FLAT` (only 10 urology indicators)

## Your Tasks

### 1. Query Optimization
- The current implementation attempts to search using a single large query, which often fails with "Request URI too long" errors when using the full datasets
- Implement a solution to handle queries of any length by breaking them into appropriate batches
- **For your final submission, modify main.py to use the full datasets**: `HEMOSTATIC_DEVICES_FLAT` and `UROLOGY_INDICATORS_FLAT`

### 2. Performance Enhancement
- The current retrieval process (`search_pmc` function) is inefficient for large result sets as it:
  - Doesn't implement proper batching (tries to get all results at once)
  - Doesn't handle pagination properly
  - Makes no use of parallel processing
  - Doesn't have retry logic for failed requests due to network errors or API rate limits
- Implement proper batching, error handling, and parallel processing to improve performance

### 3. Bonuses (Optional)

#### 1. Feature Extension
- Add support for searching PubMed in addition to PMC
  - Implement proper merging and deduplication of results from both databases
  - Ensure the solution gracefully handles API rate limits and network errors

#### 2. Cross-database Deduplication
- Be aware that the same article may exist in both PMC and PubMed databases
  - An article may have a PMCID in the PMC database but be missing its PMID
  - The same article in PubMed might have both the PMID and PMCID
  - Your solution should properly deduplicate results across databases to avoid counting the same article multiple times
#### 3. QoL Improvements
  - **Implement logging**: Replace print statements with a proper Python logging configuration
    - Use appropriate log levels
    - **Progress tracking**: Add a progress bar or status updates for long-running operations

#### 4. New Features/Improvements
- You can surprise us with new features or improvements that you think would be beneficial for this task

## Requirements

- Your solution should process queries of any length without errors
- Large result sets (10,000+ articles) should be handled efficiently
- Code should include proper error handling and logging
- Implementation should be well-documented and maintainable
- Include a brief explanation of your approach and any performance improvements achieved
- **Your code will be evaluated on different year ranges beyond just 2023**, so ensure it works for any date range
- **You are free to modify existing functions and create new ones as needed** - the focus is on developing the most efficient and robust solution.

## Evaluation Criteria

- **Correctness**: Does the solution properly handle all edge cases?
- **Performance**: How efficiently does it retrieve and process results?
- **Code Quality**: Is the code well-structured, documented, and maintainable?
- **Problem Solving**: How effectively did you identify and address the core issues?

## Resources

- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [E-utilities Quick Start](https://www.ncbi.nlm.nih.gov/books/NBK25500/)
- [ESearch Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch)
- [ESummary Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary)

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the current implementation:
   ```
   python main.py
   ```

3. Examine the limitations and errors encountered when working with larger datasets

## Submission

Please provide:
1. Your modified code
2. A brief explanation (in a separate README or comments) of:
   - Your approach to solving each task
   - Any design decisions you made and why
   - Performance metrics and improvements achieved
3. Results should be saved to the `submission_results/retrieved_ids.json` file

Good luck!