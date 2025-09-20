import bibtexparser
from bibtexparser.bparser import BibTexParser
from pathlib import Path
import re
from datetime import datetime


# Target BibTeX file
TARGET = Path("my-papers.bib")

# Configuration
SELF_NAMES = ["James Doss-Gollin", "J. Doss-Gollin"]
GROUP_MEMBERS = ["Yuchen Lu", "Lu, Yuchen"]

# Statistics tracking
IMAGE_STATS = {
    "existing_images": 0,
    "no_images": 0
}


def citekey_to_string(citekey):
    """Sanitize the citekey to generate a valid filename."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", citekey)


def escape_yaml_string(value):
    """Escape characters in a string to make it valid for YAML."""
    return value.replace(r"\&", "&").replace(r"\:", ":")


def format_title(title):
    """Format the title using titlecase except for content inside curly braces."""
    if not title:
        return title

    # Iteratively convert double curly braces to single
    while "{{" in title and "}}" in title:
        title = title.replace("{{", "{").replace("}}", "}")

    # Extract content inside curly braces and replace with placeholders
    preserved_texts = re.findall(r"{(.*?)}", title)
    for idx, text in enumerate(preserved_texts):
        placeholder = f"_p{idx}"
        title = title.replace("{" + text + "}", placeholder)

    # Use title case on the rest
    title = title.title()

    # Replace placeholders with original text from curly braces
    for idx, text in enumerate(preserved_texts):
        placeholder = f"_p{idx}"
        title = title.replace(placeholder, text)

    return title


def format_author_name(name):
    """Format the author name considering both 'lastname, firstname' and detailed formats."""
    if "family=" in name and "given=" in name:
        family = re.search(r"family=([^,]+)", name).group(1).strip()
        given = re.search(r"given=([^,]+)", name).group(1).strip()
        prefix = ""
        if "prefix=" in name:
            prefix = re.search(r"prefix=([^,]+)", name).group(1).strip()
            use_prefix = re.search(r"useprefix=([^,]+)", name).group(1).strip()
            if use_prefix == "true":
                family = prefix + " " + family
        formatted_name = given + " " + family
    elif "," in name:
        last, first = name.split(",", 1)
        formatted_name = first.strip() + " " + last.strip()
    else:
        formatted_name = name

    # Apply formatting based on name
    if any(formatted_name == self_name or formatted_name.replace("-", "") == self_name.replace("-", "") for self_name in SELF_NAMES):
        return f"**{formatted_name}**"
    elif formatted_name in GROUP_MEMBERS:
        return f"*{formatted_name}*"
    else:
        return formatted_name


def format_date(date):
    """Format the date to be in the form YYYY-MM-DD."""
    try:
        year = int(date)
        return date + "-01-01"
    except:
        return date


def extract_year(date):
    """Extract year from date string or integer."""
    try:
        if isinstance(date, int):
            return date
        elif isinstance(date, str):
            return int(date.split("-")[0])
    except:
        return None




def find_existing_image(entry):
    """Find existing image for entry."""
    citekey = citekey_to_string(entry["ID"])
    assets_dir = Path("_assets/img/pubs")

    # Check for existing images
    for extension in ["png", "jpg", "jpeg"]:
        image_path = assets_dir / f"{citekey}.{extension}"
        if image_path.exists():
            IMAGE_STATS["existing_images"] += 1
            return f"../../{image_path}"

    IMAGE_STATS["no_images"] += 1
    return None


def get_details_from_entry(entry):
    """Retrieve the details field based on the entry type."""
    if entry["ENTRYTYPE"] == "article":
        return entry.get("journaltitle", "")
    elif entry["ENTRYTYPE"] == "inproceedings":
        if "booktitle" in entry:
            return entry["booktitle"]
        elif "eventtitle" in entry and "publisher" in entry:
            return entry["publisher"] + " " + entry["eventtitle"]
        elif "eventtitle" in entry:
            return entry["eventtitle"]
        else:
            return ""
    else:
        return entry.get("howpublished", "")


def write_metadata_to_qmd(entry, qmd_file):
    """Write the metadata of a BibTeX entry to a QMD file."""
    # Initial metadata separator
    qmd_file.write("---\n")

    # Title
    qmd_file.write(
        f"title: \"{format_title(escape_yaml_string(entry.get('title', '')))}\"\n"
    )

    # Author
    authors = entry.get("author", "").split(" and ")
    qmd_file.write("author:\n")
    for author in authors:
        formatted_author = format_author_name(author.strip())
        if formatted_author.startswith("**") or formatted_author.startswith("*"):
            qmd_file.write(f'  - "{formatted_author}"\n')
        else:
            qmd_file.write(f"  - {formatted_author}\n")

    # Date
    date = format_date(entry.get("date", ""))
    qmd_file.write(f"date: {date}\n")

    # Details
    details = format_title(escape_yaml_string(get_details_from_entry(entry)))
    qmd_file.write(f'details: "{details}"\n')

    # Year (separate field for filtering/sorting)
    year = extract_year(entry.get("date", ""))
    if year:
        qmd_file.write(f"year: {year}\n")

    # Enhanced metadata for articles
    if entry["ENTRYTYPE"] == "article":
        if "volume" in entry:
            qmd_file.write(f"volume: \"{entry['volume']}\"\n")
        if "number" in entry or "issue" in entry:
            issue = entry.get("number", entry.get("issue", ""))
            qmd_file.write(f'issue: "{issue}"\n')
        if "pages" in entry:
            qmd_file.write(f"pages: \"{entry['pages']}\"\n")

    # Bibliography configuration
    citekey = entry["ID"]
    qmd_file.write(f'bibliography: ../../my-papers.bib\n')
    qmd_file.write(f'csl: ../../american-geophysical-union.csl\n')
    qmd_file.write(f'nocite: "@{citekey}"\n')

    # Image (find existing)
    image_path = find_existing_image(entry)
    if image_path:
        qmd_file.write(f"image: {image_path}\n")

    # Use the about template
    qmd_file.write("\nabout:\n")
    qmd_file.write("  template: solana\n")

    # Links
    if "doi" in entry or "repo" in entry or "preprint" in entry or "url" in entry:
        qmd_file.write("  links:\n")

    # DOI
    if "doi" in entry:
        doi = entry["doi"]
        is_open = entry.get("open", "") == "true"
        if is_open:
            qmd_file.write(f"    - text: 'DOI: {doi} (Open Access)'\n")
        else:
            qmd_file.write(f"    - text: 'DOI: {doi}'\n")
        qmd_file.write(f"      href: https://doi.org/{entry['doi']}\n")
        qmd_file.write(f"      icon: link\n")

    elif "url" in entry:
        url = entry["url"]
        is_open = entry.get("open", "") == "true"
        qmd_file.write(f"    - href: {url}\n")
        qmd_file.write(f"      icon: link\n")
        if is_open:
            qmd_file.write(f"      text: 'Open Access'\n")
        else:
            qmd_file.write(f"      text: 'Link'\n")

    # Repository
    if "repo" in entry:
        qmd_file.write("    - icon: github\n")
        qmd_file.write("      text: Code\n")
        qmd_file.write(f"      href: {entry['repo']}\n")

    # Preprint
    if "preprint" in entry:
        qmd_file.write("    - text: Preprint\n")
        qmd_file.write(f"      icon: file-pdf\n")
        qmd_file.write(f"      href: {entry['preprint']}\n")

    # End of metadata
    qmd_file.write("\nformat:\n  html:\n    page-layout: full\n")
    qmd_file.write("---")

    # Abstract
    if "abstract" in entry:
        qmd_file.write("\n\n")
        qmd_file.write(entry["abstract"])
    
    # Original BibTeX entry (without abstract)
    qmd_file.write("\n\n## BibTeX\n\n```bibtex\n")
    qmd_file.write(f"@{entry['ENTRYTYPE']}{{{entry['ID']},\n")
    
    for key, value in entry.items():
        if key not in ['ENTRYTYPE', 'ID', 'abstract']:  # Skip abstract
            qmd_file.write(f"  {key} = {{{value}}},\n")
    
    qmd_file.write("}\n```")


def entry_to_qmd(entry):
    """Convert a BibTeX entry to QMD format."""
    citekey = citekey_to_string(entry["ID"])

    # Determine the directory based on the entry type
    if entry["ENTRYTYPE"] == "article":
        directory = "publications/article"
    elif entry["ENTRYTYPE"] == "inproceedings":
        directory = "publications/conference"
    elif entry["ENTRYTYPE"] in ["online", "preprint"]:
        directory = "publications/forthcoming"
    else:
        directory = "publications/other"

    qmd_filename = Path(directory, f"{citekey}.qmd")
    qmd_filename.parent.mkdir(parents=True, exist_ok=True)

    with open(qmd_filename, "w") as qmd_file:
        write_metadata_to_qmd(entry, qmd_file)


def create_qmd_from_bib(bib_file):
    """Create QMD files from BibTeX file."""
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False

    with open(bib_file, "r") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    for entry in bib_database.entries:
        entry_to_qmd(entry)


def clean_publication_directories():
    """Clean up existing QMD files and ensure directories exist."""
    base_dir = Path("publications")
    total_removed = 0

    # Clean up existing QMD files
    for dir_name in ["article", "conference", "other", "forthcoming"]:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            removed_count = len(list(dir_path.glob("*.qmd")))
            for file in dir_path.glob("*.qmd"):
                file.unlink()
            total_removed += removed_count
            if removed_count > 0:
                print(f"Removed {removed_count} QMD files from {dir_path}")
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

    if total_removed > 0:
        print(f"Total files removed: {total_removed}")

    # Ensure assets directory exists
    assets_dir = Path("_assets/img/pubs")
    assets_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("Starting BibTeX to QMD conversion...")

    # Clean up and prepare directories
    clean_publication_directories()

    # Create QMD files from BibTeX
    create_qmd_from_bib(TARGET)
    
    # Print summary statistics
    print("\n" + "="*50)
    print("CONVERSION SUMMARY")
    print("="*50)
    print(f"QMD files generated in publications/ directories.")
    print(f"\nImage Status:")
    print(f"  ✓ Existing images found: {IMAGE_STATS['existing_images']}")
    print(f"  ○ No images:             {IMAGE_STATS['no_images']}")
    print(f"  Total publications:      {sum(IMAGE_STATS.values())}")
    print("="*50)
