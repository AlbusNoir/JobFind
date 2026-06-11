# Job Search CLI Tool

A Python CLI application that searches the web for jobs, evaluates and sorts them, and displays them in a clean, auto-wrapped terminal table. Uses [`python-jobspy`](https://pypi.org/project/python-jobspy/) under the hood to search major job boards (Currently: LinkedIn, Indeed, Glassdoor, and ZipRecruiter). It also features a "smart synopsis extractor" (or a "filter out the non-relevant stuff") that filters out company introductions, boilerplate, prattling, etc. 

---

## Features

- **Run it one of two ways**: Can be ran interactively via the terminal or by passing a config file (see included [config.txt](/config.txt) as an example)
- **Smart Synopsis Extraction**: Logic that aims to bypass corporate intro fluff, stocks/tickers, and generic preambles to pull the actual job duties
- **Keyword Scoring and Deduplication**: Deduplicates listings across boards and ranks them based on how closely their titles and descriptions match your search keywords (helps to weed out things that matched your keywords but aren't actually related)
- **CSV Export**: Will offer to save the file to a CSV by default. Which I guess could be helpful for tracking jobs? It currently overwrites the file so there'd have to be more logic here for long-term tracking...
- **Unit Tests**: The stuff nobody really looks at but still exists to sanity check the application. I've included them for troubleshooting

---

## Prerequisites

- **Python**: Version 3.10 or higher is required by `python-jobspy`  

> [!NOTE]
> Written and tested in Python 3.12  
> Wheels broke trying to install numpy on 3.14. So you can try that too, might work in the future once that's updated more
> 
> I used [uv](https://github.com/astral-sh/uv). So go download that. Or don't. You can install the reqs either way. I've included them via a requirements.txt file to be useable by anyone, uv or not. 

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd JobFind
   ```

2. **Create a virtual environment and install dependencies using (using `uv` or not, your choice)**:
   ```bash
   uv venv --python 3.12
   uv pip install -r requirements.txt

   OR

   python -m venv .venv
   source .venv/bin/activate
   pip install -r
   ```
   *Completely ignore the above if you're feeling spicy and like installing things system-wide (please don't)*

---

## How to Run

### 1. Interactive Mode
Run the script without arguments. It will guide you through entering your keywords, location, and search radius:
```bash
python job_search.py
```

### 2. Configuration File Mode
Create a text file (name doesn't matter) containing your search parameters in the following format:
```text
location: City, State
radius: 25 miles
keywords: it, technology, network, helpdesk, support
```
Then pass the path to the file as an argument:
```bash
python job_search.py whatever-you-named-it.txt
```

---

## Running Tests

If stuff is broken, try running the unit tests to figure out what/why (probably not how):
```bash
python -m unittest test_job_search.py
```

---

## Contributing

Contributions are welcome, but not expected. If you would like to contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b whatever-you-want-to-name-it`).
3. Commit your changes with something descriptive/clever(`git commit -m 'Original is a dud so I fixed it'`).
4. Push to the branch (`git push origin whatever-you-named-it-above`).
5. Open a **PR**.

If you encounter any bugs or have feature requests, you can open an **Issue** but I don't know that this will be a long-running project.

---

## License

[MIT License](/LICENSE)
