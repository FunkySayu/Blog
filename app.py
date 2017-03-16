#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

import os
from glob import glob
from os.path import basename
import subprocess
from flask import Flask, render_template, abort, g

app = Flask(__name__)
app.secret_key = os.urandom(128)

DEBUG = False

COMMAND_LINE_CALL = ["ipython", "nbconvert", "--to", "html", "--template", "basic"]
BASE_DIRECTORY = "/srv/funkysayu.fr/src"


@app.before_request
def before_request():
    nbk_dir = os.path.join(BASE_DIRECTORY, 'notebooks') + os.sep
    g.articles = {basename(f): int(os.path.getmtime(f))
                  for f in glob(nbk_dir + "*.ipynb")}


def get_notebook(notebook_name):
    """Get the notebook and convert it if needed
    """
    notebook_path = os.path.join(BASE_DIRECTORY, "notebooks", notebook_name)
    if not os.path.exists(notebook_path):
        abort(404)

    export_path = os.path.join(BASE_DIRECTORY, "_rendered", ".".join(notebook_name.split(".")[:-1]) + ".html")
    # Remove if there's a new modification
    if os.path.exists(export_path) and os.path.getmtime(notebook_path) > os.path.getmtime(export_path):
        os.remove(export_path)

    # Create if not exists
    if not os.path.exists(export_path):
        subprocess.check_call(COMMAND_LINE_CALL + [notebook_path, "--output", export_path])

    # Raise if not exists
    if not os.path.exists(export_path):
        abort(500)

    with open(export_path) as f:
        content = f.read().decode("utf-8")

    return content


@app.route("/")
def index():
    articles = sorted(g.articles.keys(), key=g.articles.get, reverse=True)
    return render_template('index.html', articles=[get_notebook(basename(n)) for n in articles[:3]])


@app.route("/notebooks")
def list_notebooks():
    result = {}

    for nb_name, nb_date in g.articles.items():
        year = datetime.datetime.fromtimestamp(nb_date).year
        if year not in result:
            result[year] = [nb_name]
        else:
            result[year].append(nb_name)

    result = {y: sorted(n, key=g.articles.get, reverse=True) for (y, n) in result.items()}
    return render_template("notebooks.html", notebook_per_years=result, sorted=sorted)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/projects")
def projects():
    return render_template("projects.html")


@app.route("/notebooks/<notebook_name>")
def notebook(notebook_name):
    """Dynamically render IPython Notebook
    """
    content = get_notebook(notebook_name)

    return render_template('notebook.html', content=content, name=notebook_name)


@app.route("/update/sources", methods=["POST"])
def update():
    """Update sources from the git by pulling them.
    """
    subprocess.check_output(["git",  "pull", "origin", "master"])
    return "OK"


@app.route("/update/notebooks", methods=["POST"])
def update_notebooks():
    """Git pull powa v2.
    """
    subprocess.check_output(["git", "pull", "notebooks", "master"])
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=DEBUG, port=6000)
