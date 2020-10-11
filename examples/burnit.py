import jinja2
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

EXAMPLES_DIRECTORY = Path(__file__).parent
MARKDOWN_DIRECTORY = EXAMPLES_DIRECTORY.parent / "docs" / "markdown" / "examples"


def create_example(section_name):

    env = Environment(loader=FileSystemLoader(EXAMPLES_DIRECTORY), keep_trailing_newline=True)

    template = env.get_template(f"{section_name}.jinja")

    example_files = EXAMPLES_DIRECTORY.glob("*.py")

    filtered_files = list(filter(lambda f: f"{section_name}" in f.name, example_files))

    examples = []
    for bf in filtered_files:
        with open(bf, mode="r") as file:
            examples.append(file.read().split("\n"))

    def strip_docstrings(line):
        return line.strip("#").replace("title:", "").replace("note:", "").strip()

    sections = []
    for ex in examples:
        exdict = {"title": None, "body": [], "note": None}
        for idx, line in enumerate(ex):
            if "title:" in line:
                exdict["title"] = strip_docstrings(line)
            elif "note:" in line:
                exdict["note"] = strip_docstrings(line)
            else:
                exdict["body"].append(line)

        sections.append(exdict)

    output = template.render(sections=sections)

    with open(MARKDOWN_DIRECTORY / f"{section_name}_example.md", mode="w") as file:
        file.write(output)


if __name__ == "__main__":
    create_example("basics")
    create_example("extra")
