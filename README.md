# newsreader-docker
Dockerfile to construct the Newsreader pipeline.

## Purpose

This repo is a sequel from the
[Newsreader project](http://www.newsreader-project.eu/). In this
project an NLP pipeline has been developed to annotate texts. Version
3 of this pipeline has been used successfully to annotate millions of
newspaper-size documents. However, there are issues that can be
improved and this repo serves as a proof-of-concept for a new version
of the pipeline. It addresses the following issues:

1. To build the pipeline from open-source components that can be
   freely downloaded from Internet.
2. To ensure reproducibility of the annotion process i.e. to enable to
   rebuild an identical pipeline in some point in the future.
3. To standardize the installation and use of the modules.

The pipeline uses the Newsreader Annotation Format
([NAF](https://github.com/newsreader/NAF)) to store the annotated
texts.

The full documentation of this project is still under construction.

## What does it build?

With this repo a Docker image can be built that supplies an API. The
user can submit a Dutch or English text in the form of plain text or
as a "raw" naf and obtain a NAF file with the annotated text.



## Installation

1. Clone this repository.
2. Some of the modules are not yet open-source. Therefore you need a
   key in file `nrkey`. Contact the author to obtain this key and
   place it in the `newsreader-docker/repo` directory.
3. Build the image: `cd` to `newsreader-docker` and perform 
   `./doit`.
4. When al goes well, this would result in a running container with a
   ready-to-use API. However, things do not go well yet, so a new
   container has to be started. So, when the build process is ready,
   perform `docker run -i -p 5002:5002 -t newsreader-docker
   /bin/bash`. When this goes well you end up with a command-line
   interface to the docker container.
5. One of the modules can currently only be run in server mode. Tot start
   the server, perform
   `/usr/local/nlpp/nlppmodules/EHU-srl-server/run-server.sh`.
6. When the server runs, start the web-server.
   Do `python /usr/local/nlpp/server/server.py --host 0.0.0.0 --port 5002 --debug`.

## Usage

When the server runs, load URL `http://localhost:5002` in your
browser. This results in a page that lists the supported API calls and that
enables to type in and submit a Dutch or English text or to upload a "raw"
NAF file. When all goes well, after seconds or a few minutes the NAF
file with the annotated text will appear. 
