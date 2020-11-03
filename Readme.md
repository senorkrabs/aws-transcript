# Transcript.py
Proof-of-concept python script that can process Amazon Transcribe JSON documents and generate CSV, TSV, and HTML files as output.

## Usage
```
$ python transcript.py -h
usage: transcript.py [-h] --path PATH [PATH ...] [--results-dir RESULTS_DIR] [--csv] [--tsv] [--html]

Parses transcription JSON documents produced by AWS Transcribe and generates timestamped CSV, TSV, and HTML files with speaker/channel labels and confidence scores.

optional arguments:
  -h, --help            show this help message and exit
  --path PATH [PATH ...]
                        The path containing the transcription files. Supports glob pattern matching.
  --results-dir RESULTS_DIR
                        The directory where the results will be written. Defaults to the ./results/
  --csv                 Generate a CSV for each transcription.
  --tsv                 Generate a TSV for each file.
  --html                Generate a HTML for each file.

NOTES: The script expects the JSON document to be from AWS Transcribe. It extracts the first transcription from each item. Other alternatives are ignored. Rows are separated by speaker/channel changes. If     
the transcription doesn't contain speakers/channels then rows are separated by punctuation.
```

## Future Enhancements?
- Move transcription parser into a separate class to make it reusable with other projects
