# From Insights to Impact: Actionable Interpretability for Neural Machine Translation

This repository contains the full contents of my PhD thesis, written in Quarto and supporting cross-compilation to PDF and HTML formats. It is based on the excellent [GroNLP](https://www.rug.nl/research/clcg/?lang=en) thesis template by [Rik van Noord](https://www.rikvannoord.nl/), which was adapted to work with Quarto by [Gabriele Sarti](https://gsarti.com). The template can be easily adapted for other thesis requirements by adjusting the `_quarto.yaml` file and the templates in the `latex` folder.

## Requirements

- [Quarto](https://quarto.org/docs/get-started/) (>= 1.0)
- [R](https://cran.r-project.org/) (>= 4.0)

Run the following command to install the required R packages:

```shell
./setup.sh
```

## Why bother?

The most significant advantage of using Quarto over writing plain LaTeX is the supported **cross-compilation** to HTML and PDF formats. Having used RMarkdown for writing my [masters' thesis](https://github.com/gsarti/masters-thesis), I was already familiar with Bookdown and migrating to Quarto was a breeze. However, for someone approaching this for the first time, writing with Quarto can come at the cost of fiddling with edge cases, writing most content in Markdown, and converting tables to be available in both LaTeX and HTML formats. Be mindful of these overhead efforts before deciding to pick Quarto for your thesis!

You can have a look at the [web version of my thesis](https://gsarti.com/phd-thesis) for an example of a finished book looks like.

## Usage

To build the thesis in its PDF form, run the following command:

```shell
make pdf
```

To build the thesis in its HTML form, run the following command:

```shell
make web
```
