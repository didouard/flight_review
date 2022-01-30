#! /usr/bin/env python3
""" Script to download public logs """

import os
import glob
import argparse
import json
import datetime
import sys
import time

import requests

from plot_app.config_tables import *


def get_arguments():
    """Get parsed CLI arguments"""
    parser = argparse.ArgumentParser(
        description="Python script for downloading public logs "
        "from the PX4/flight_review database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_entries",
        help="Whether to only print (not download) the database entries.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default="./",
        help="The directory to look for ulog file.",
    )
    parser.add_argument(
        "--db-info-api",
        type=str,
        default="https://review.px4.io/dbinfo",
        help="The url at which the server provides the dbinfo API.",
    )
    parser.add_argument(
        "--upload-api",
        type=str,
        default="https://review.px4.io/dbinfo",
        help="The url at which the server provides the upload API.",
    )
    parser.add_argument(
        "--source",
        default=None,
        type=str,
        help='The source of the log upload. e.g. ["webui", "CI"]',
    )
    return parser.parse_args()


def main():
    """main script entry point"""
    args = get_arguments()

    try:
        # the db_info_api sends a json file with a list of all public database entries
        db_entries_list = requests.get(url=args.db_info_api).json()
    except:
        print("Server request failed.")
        raise

    if args.print_entries:
        # only print the json output without downloading logs
        print(json.dumps(db_entries_list, indent=4, sort_keys=True))

    else:
        # find already existing logs in download folder
        logfile_pattern = os.path.join(os.path.abspath(args.directory), "*.ulg")
        logfiles = glob.glob(os.path.join(os.getcwd(), logfile_pattern))
        logids = [os.path.basename(f) for f in logfiles]

        # sort list order to first download the newest log files
        db_entries_list = sorted(
            db_entries_list,
            key=lambda x: datetime.datetime.strptime(x["log_date"], "%Y-%m-%d"),
            reverse=True,
        )

        already_uploaded_file = [f["original_filename"] for f in db_entries_list]

        for filename, logfile in zip(logids, logfiles):
            if filename in already_uploaded_file:
                print(f"[skip] Already uploaded : {filename}")
                continue

            file = {"filearg": (filename, open(logfile, "rb"))}
            values = {
                "source": "uploader",
                "type": "simple_log",
                "description": "",
                "email": "",
                "allowForAnalysis": "true",
            }

            r = requests.post(url=args.upload_api, files=file, data=values)

            if r.status_code == 200:
                data = json.loads(r.text)
                url = data["url"]
                print(f"Uploaded : {logfile}, url: {url}")


if __name__ == "__main__":
    main()
