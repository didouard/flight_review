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
        "--server",
        type=str,
        default="http://localhost:5006",
        help="The url of the server",
    )
    parser.add_argument(
        "--name",
        default=None,
        type=str,
        help="Name of the show",
    )
    parser.add_argument(
        "--show_id",
        default=None,
        type=str,
        help="Id of the show",
    )
    return parser.parse_args()


def main():
    """main script entry point"""
    args = get_arguments()

    try:
        # the db_info_api sends a json file with a list of all public database entries
        db_entries_list = requests.get(url=args.server + "/dbinfo").json()

        if not args.show_id:
            values = {"name": args.name, "place": "jn", "datetime": "12345567789"}
            url = args.server + "/show"
            r = requests.post(url=url, data=values).json()
            show_id = r["id"]
        else:
            show_id = args.show_id

    except Exception as e:
        print("Server request failed.")
        print(e)
        raise

    if args.print_entries:
        # only print the json output without downloading logs
        print(json.dumps(db_entries_list, indent=4, sort_keys=True))
        return

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
            "shows_id": show_id,
            "source": "uploader",
            "type": "simple_log",
            "description": "",
            "email": "",
            "allowForAnalysis": "true",
        }

        r = requests.post(url=args.server + "upload", files=file, data=values)

        if r.status_code == 200:
            data = json.loads(r.text)
            url = data["url"]
            print(f"Uploaded : {logfile}, url: {url}")


if __name__ == "__main__":
    main()
