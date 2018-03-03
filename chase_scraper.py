import csv
import itertools
import re
import sys

import requests
import tqdm


COOKIE_VALUE = None


def _get_page(relative_url):
    assert COOKIE_VALUE
    return requests.get('https://cards.chase.com' + relative_url,
                        cookies={'SMSESSION': COOKIE_VALUE}).text


def scrape_stuff():
    # URL from going to "blueprint", "track it", watching console
    start_page_html = _get_page(
        '/CC/BluePrint/TrackIt/SpendingReport/623183308')
    relevant_line = next(line for line in start_page_html.splitlines()
                         if 'Categories' in line)

    detail_links = list(re.finditer(
        r'''title="([^"]*)" href="#" onclick="[^,"]*,'''
        r"'(/CC/BluePrint/TrackIt/CategoryDetails/[^']*)'",
        relevant_line))

    for match in tqdm.tqdm(detail_links):
        category = match.group(1)
        detail_page = _get_page(match.group(2))
        cycle_links = itertools.chain(*[
            [m.group(1).replace('&amp;', '&')
             .replace('Current Cycle', '00000000')
             for m in re.finditer(r'<area [^>]*(/CC/BluePrint/TrackIt/'
                                  r'GetTransactions[^,]*)&#39;,',
                                  detail_page)]])
        cycle_pages = map(_get_page, cycle_links)
        for page in cycle_pages:
            if 'There are no purchases' in page:
                continue
            tbody = page.split('<tbody>')[1]
            for row in tbody.split('</tr>')[:-1]:  # strip trailing junk
                row = row.split('>', 1)[1]  # strip <tr>
                yield ([
                    cell.split('>', 1)[1]  # strip <td>
                    for cell in row.split('</td>')[:-1]  # strip trailing ''
                ] + [category])

    if not _get_page('/CC/BluePrint/TrackIt/SpendingReport/623183308'):
        raise RuntimeError("Your cookie ran out!  Try again :(")


def main():
    global COOKIE_VALUE
    COOKIE_VALUE = raw_input("Your SMSESSION cookie, please: ")
    with open(sys.argv[1], 'w') as f:
        csv.writer(f).writerows(scrape_stuff())


if __name__ == '__main__':
    main()
