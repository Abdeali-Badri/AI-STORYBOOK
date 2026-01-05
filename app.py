from flask import Flask, render_template, request, redirect, url_for, send_file
from pathlib import Path

# IMPORT YOUR PIPELINE FUNCTIONS
from gist_to_story import generate_story_with_moral
from split_pages import split_pages

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "static" / "pdf" / "storybook.pdf"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    gist = request.form.get("gist", "").strip()

    if not gist:
        return "Story idea is required", 400

    try:
        # Generate story
        story_data = generate_story_with_moral(gist)

        #  Split into pages
        split_pages(story_data)

        # Generate images
        import image_generator
        image_generator.main()

        # Generate PDF
        import pdf_generator
        pdf_generator.main()

    except Exception as e:
        return f"Error while generating storybook: {e}", 500

    return redirect(url_for("download"))

@app.route("/download", methods=["GET"])
def download():
    if not PDF_PATH.exists():
        return "PDF not found. Generate the story first.", 404

    return send_file(
        PDF_PATH,
        as_attachment=True,
        download_name="storybook.pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)

