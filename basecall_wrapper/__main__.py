#!/usr/bin/env python3

import argparse
import datetime
import io
import os
from pkg_resources import resource_filename
from psutil import virtual_memory
import subprocess
import sys
import snakemake


# FUNCTIONS
def generate_message(message_text):
    """Format messages with date and time"""
    now = datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')
    print('[ %s ]: %s' % (now, message_text))


def print_graph(snakefile, config, dag_file):
    # store old stdout
    stdout = sys.stdout
    # call snakemake api and capture output
    sys.stdout = io.StringIO()
    snakemake.snakemake(
        snakefile,
        config=config,
        dryrun=True,
        printdag=True)
    output = sys.stdout.getvalue()
    # restore sys.stdout
    sys.stdout = stdout
    # pipe the output to dot
    with open(dag_file, 'wb') as svg:
        dot_process = subprocess.Popen(
            ['dot', '-Tsvg'],
            stdin=subprocess.PIPE,
            stdout=svg)
        dot_process.communicate(input=output.encode())


def main():
    # GLOBALS
    snakefile = resource_filename(__name__, 'config/Snakefile')

    # parse fasta file from command line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        required=True,
        help='.tar.gz files containing raw Nanopore data folders',
        type=str,
        dest='raw_data',
        action='append')
    parser.add_argument(
        '--outdir',
        required=True,
        help='Output directory',
        type=str,
        dest='outdir')
    parser.add_argument(
        '--flowcell',
        required=True,
        help='Flowcell type, e.g. FLO-MIN106',
        type=str,
        dest='flowcell')
    parser.add_argument(
        '--kit',
        required=True,
        help='Sequencing kit, e.g. SQK-RAD003',
        type=str,
        dest='kit')
    default_threads = min(os.cpu_count() // 2, 50)
    parser.add_argument(
        '--threads',
        help=('Number of threads. Default: %i' % default_threads),
        type=int,
        dest='threads',
        default=default_threads)
    default_mem = int(virtual_memory().free * 0.5 // 1e9)
    parser.add_argument(
        '--memory',
        help=('Memory limit. Default: %i' % default_mem),
        type=int,
        dest='memory',
        default=default_mem)

    args = vars(parser.parse_args())

    # set up logging
    outdir = args['outdir']
    log_dir = os.path.join(outdir, 'logs')
    args['log_dir'] = log_dir
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    # print before dag
    print_graph(snakefile, args, os.path.join(log_dir, "before.svg"))

    # run the pipeline
    snakemake.snakemake(
        snakefile=snakefile,
        config=args,
        cores=args['threads'],
        timestamp=True)

    # print after dag
    print_graph(snakefile, args, os.path.join(log_dir, "after.svg"))


if __name__ == '__main__':
    main()
