from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
"""
Very simple web server for Newsreader:
/                 GET   Generate a form.
/text/            GET   idem.
/text/<lang>      GET   Process text in argument or generate form.
/text/<lang>/text GET   Process "text"
/text/<lang>      POST  Process text in argument.
/naf              POST  Process argument as input naf.
"""

import sys
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

import os

server_dirname = os.path.dirname(os.path.realpath(sys.argv[0]))
nlpp_dirname = os.path.dirname(server_dirname)
bin_dirname = os.path.join(nlpp_dirname, "bin")

import subprocess
import tempfile
import logging

from flask import Flask, request, redirect, url_for, jsonify, Response, flash
from werkzeug.utils import secure_filename


app = Flask('NewsreaderServer')

@app.route('/', methods=['GET'])
@app.route('/text', methods=['GET'])
def index():
    return the_form(), 200

@app.route('/text/<lang>', methods=['GET'])
def parse_text_arg(lang):
    if not ((lang == 'nl') or (lang == 'en')):
        return "Cannot process language {}".format(lang), 400
    text = request.args.get('text', None)
#    output = request.args.get('output', "dependencies")
    if not text:
        return the_form(), 400
    in_naf = text2naf(text, lang)
    result = naf2naf(in_naf)
    return Response(result, mimetype='text/xml')

@app.route('/text/<lang>', methods=['POST'])
def parse_text_arg_post(lang):
    if not ((lang == 'nl') or (lang == 'en')):
        return "Cannot process language {}".format(lang), 400
    body = request.get_json(force=True)
    text = body['text']
    in_naf = text2naf(text, lang)
    result = naf2naf(in_naf)
    return Response(result, mimetype='text/xml')


@app.route('/text/<lang>/<text>', methods=['GET'])
def parse_text_url(lang, text):
    if not ((lang == 'nl') or (lang == 'en')):
        return "Cannot process language {}".format(lang), 400
#    text = request.args.get('text', None)
#    output = request.args.get('output', "dependencies")
    if not text:
        return "Usage: /text/lang/text", 400
    in_naf = text2naf(text, lang)
    result = naf2naf(in_naf)
    return Response(result, mimetype='text/xml')


@app.route('/naf', methods=['POST'])
def parse_naf():
    # check if the post request has the file part
    if 'naf' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['naf']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        naffile = request.files['naf']
        nafstr = naffile.read().decode("utf-8")
        result=naf2naf(nafstr)
    return Response(result, mimetype='text/xml')
 

def the_form():
    with open(os.path.join(server_dirname, 'form.html')) as f:
        helptext = f.read()
    return helptext

def text2naf(text, lang):
    cmd = ["bash", os.path.join( bin_dirname, "text2anaf.sh"), lang]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _err = p.communicate(text.encode("utf-8"))
    retcode = p.poll()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output

def naf2naf(innaf):
    cmd = ["bash", "nlpp"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _err = p.communicate(str(innaf).encode("utf-8"))
    retcode = p.poll()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


if __name__ == '__main__':
    app.run(port=5002, host="0.0.0.0", debug=True)
#    import argparse
#    import tempfile

#    parser = argparse.ArgumentParser()
#    parser.add_argument("--port", "-p", type=int, default=5002,
#                        help="Port number to listen to (default: 5001)")
#    parser.add_argument("--host", "-H", help="Host address to listen on (default: localhost)")
#    parser.add_argument("--debug", "-d", help="Set debug mode", action="store_true")
#    args = parser.parse_args()

##    logging.basicConfig(level=logging.DEBUG if (args.debug or args.verbose) else logging.INFO,
#    logging.basicConfig(level=logging.DEBUG if (args.debug) else logging.INFO,
#                        format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')
#
#    app.run(port=args.port, host=args.host, debug=args.debug)
