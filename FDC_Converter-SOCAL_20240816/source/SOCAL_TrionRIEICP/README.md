# FDC Script SOCAL Trion RIE ICP
## Overview
This Python script is designed to process files related to FDC (Fault Detection and Classification) for a tool at SOCAL Trion RIE ICP. The script reads input files, extracts relevant information, and generates output files in a specified format. It also handles file locking to prevent concurrent execution.

## Usage

### Command-Line Arguments
 * pos1: Path to the input file directory.
 * pos2: Tool ID.
 * -outdir: Output folder path (default: "outdir/").
 * -logdir: Log folder path (default: "logdir/").
 * -refdir: Reference folder path.
 * -lockdir: Lock folder path (default: "/").
 * -ext or --extension: File extension (default: "log").

### Example
:electron: python3 FDC_Script_SOCAL_TrionRIEICP.py {{ input_folder }} {{ tool_id }} -outdir {{ output_folder }} -logdir {{ log_folder }} -ext {{ extension : log }}

### Processing Logic
 * Header Conversion: Converts special characters in the header of the sensor data file.
 * Lock File Handling: Checks for lock files to ensure exclusive access to files during processing.
 * Log File Setup: Initializes logging with a timestamped log file.
 * File Processing: Iterates through files in the input directory, processes each file, and generates output files.
 * Output XML Generation: Creates a new XML file for each processed file, incorporating relevant information.
 * Move to Processed: Moves processed files to the "Processed" folder and removes lock files.

## Requirements
 * Python 3.x
 * pandas
 * xml.etree.ElementTree
 * jinja2

## Notes
Ensure the required Python libraries are installed before running the script.
The script is designed to handle specific file formats and may need adjustments for different input structures.

## Authors
Yu-Pu Wu (PDF)

