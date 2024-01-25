# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-

import logging
import vertexai
import langchain
from google.cloud import aiplatform
from langchain.llms import VertexAI

from langchain.document_loaders import PyPDFLoader  # to load and parse PDFs
import markdown  # to format LLM output for web display

import os  # to remove temp PDF files
import uuid  # to generate temporary PDF filenames

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_bootstrap import Bootstrap5, SwitchField
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.fields import SubmitField, RadioField, TextAreaField

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = "dev"

# set default button sytle and size, will be overwritten by macro parameters
app.config["BOOTSTRAP_BTN_STYLE"] = "primary"
app.config["BOOTSTRAP_BTN_SIZE"] = "sm"

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)


class UploadForm(FlaskForm):
    """A basic form (new edit) to upload a file and take a text prompt."""

    tech_trend = TextAreaField(label="What technology trend do you want to write about?", default="")
    reading_level = RadioField("Reading level:", choices=["6th grade", "9th grade", "12th grade"], default="12th grade")
    #pdf_file = FileField(
    #    validators=[
    #        FileRequired(),
    #        FileAllowed(["pdf"], "Please select a PDF."),
    #    ],
    #    label="Select a PDF",
    #)
    #text_input = TextAreaField(label="Instructions", default="Summarize the PDF.")
    submit = SubmitField()

# initialize VertexAI
vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")

llm = VertexAI(
    model_name="text-bison@001", max_output_tokens=1024, temperature=0.7, top_p=0.5
)

@app.route("/", methods=["GET", "POST"])
def index():
    """Route to display the input form and query the LLM."""
    form = UploadForm()
    if form.validate_on_submit():
        logging.debug(f"trend: {form.tech_trend.data}")
        logging.debug(f"reading level: {form.reading_level.data}")
        #pdf_temp_filename = str(uuid.uuid4())
        #form.pdf_file.data.save(pdf_temp_filename)
        #loader = PyPDFLoader(pdf_temp_filename)
        #pages = loader.load_and_split()
        #combined_text = "\n\n".join([p.page_content for p in pages])
        #word_count = len(combined_text.split())
        #logging.debug(f"pages: {len(pages)}")
        #logging.debug(f"word_count combined: {word_count}")
        # 4800 words times ~1.66 tokens per words should keep us under text-bison's token limit
        prompt = f"""
you are a senior consultant at technology company Inforte Corp.
you only write articles about technology trends.
write an upbeat, professional article at a {form.reading_level.data} reading level about a trend in technology, specified below
1. begin with a compelling or surprising statement or question to capture the reader's interest
2. include a personal story telling how the trend has impacted you
3. provide a fact or statistic about the trend which highlights its importance / relevance
4. close with a clear call to action for the reader, directing them to your company's website (http://www.afkbrb.com)
5. include 3-4 relevant hash tags at the end of the article
technology trend: {form.tech_trend.data}"""
        logging.debug(prompt)
        response = llm(prompt)
        #response = response.replace("\n- ", "\n\n* ")
        #markdown_response = markdown.markdown(response)
        session["response"] = response
        logging.debug(f"Response: \n{response}")
        #os.remove(pdf_temp_filename)
        return redirect(url_for("ttwb_results"))
    else:
        logging.error(f"Form errors: {form.errors}")

    return render_template("index.html", upload_form=form)


@app.route("/ttwb_results", methods=["GET", "POST"])
def ttwb_results():
    """Route to display results."""

    # flash("Awaiting the model's response!")
    return render_template(
        "ttwb_results.html", response_text=session["response"]
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
