#!/usr/bin/env python3

import argparse
import json
import os
import tempfile 
from seleniumwire import webdriver
from seleniumwire.utils import decode
from urllib.parse import urlparse, urlsplit
from tqdm import tqdm
import sys
# Might neeed:  (https://github.com/seleniumbase/SeleniumBase/issues/2782)
# pip install blinker==1.7.0


def extract_domain(url: str) -> str:
    """
    Extract the network location of the url, i.e., `https://example.co.uk/foo.html -> example.co.uk`.
    """
    return urlsplit(url).netloc


def extract_file_path(url: str) -> str:
    """
    Extract the path relative to the root directory from the url, i.e., `https://foo.com/js/bar/baz.js -> js/bar/baz.js`
    """
    return urlsplit(url).path


def extract_source_file_path(url: str) -> str:
    """
    Extract the path relative to root for a JavaScript source file in the given url and ignore any content trailing the last '.js' occurrence, i.e., `https://foo.com/js/bar/baz.js.minifiedver=1012 -> js/bar/baz.js`
    """
    source_file = extract_file_path(url)
    file_path = f"{"".join(source_file.split(".js")[:-1])}.js"
    return file_path


def download_site(url: str, target_folder: str, run_headless : bool = False):
    """Visit the given url and download the JavaScript source files based on incoming traffic"""
    dir_path = target_folder + extract_domain(url)
    os.makedirs(dir_path)

    # Setup browser
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    profile_dir = tempfile.mkdtemp(prefix="benjamin-")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")            # ← NEW
    chrome_options.add_argument("--disable-dev-shm-usage") # ← NEW

    
    if run_headless:
        # https://www.selenium.dev/blog/2023/headless-is-going-away/
        # chrome_options.add_argument("--headless=new")  # new method

        # Actually back to old?
        # https://stackoverflow.com/questions/78996364/chrome-129-headless-shows-blank-window
        chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options = chrome_options)

    try:
        
        driver.get(url)


        # Save the page source, with possible inline JS
        page_source = driver.page_source.encode()
        with open(dir_path + "/index.html", "wb+") as f:
            _ = f.write(page_source)

        for request in driver.requests:
            print(request.url)

            purl = urlparse(request.url)
            if not purl.path.endswith(".js"):
                continue

            source_file = purl.netloc  + "/" + extract_source_file_path(purl.path)
            response = request.response
            if not response:
                print("No response from ", request.url)
                continue


            body = decode(
                response.body, response.headers.get("Content-Encoding", "identity")
            )
            body_str = body

            print("Making dir: ", os.path.dirname(dir_path + "/" +  source_file))
            os.makedirs(os.path.dirname(dir_path + "/" + source_file), exist_ok=True)
            with open(dir_path + "/" + source_file, "wb+") as f:
                _ = f.write(body_str)
    finally:
        driver.quit()



def main():
    cli = argparse.ArgumentParser(
        description="Download JavaScript source code from one or more websites"
    )
    cli.add_argument(
        "domain", help="Domain we aim to crawl"
    )
    cli.add_argument(
        "-o", help="Output folder for downloaded JavaScript", type=str, default="newdata/"
    )

    cli.add_argument(
        '--headless', action='store_true', help="Run in headless"
    )
    args = cli.parse_args()
    output_folder = args.o
    url = args.domain

    try:
            print("nDownloading ", url)
            download_site(url, output_folder, args.headless)
            sys.exit(0)
    except Exception as e:
            print("Failed ", e, url)
            open("errors.txt", "a+").write("Failed on " + url + "\n" + str(e) + "\n\n")
            sys.exit(1)
        # input("NEXT?")
    

if __name__ == "__main__":
    main()

