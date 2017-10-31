import requests

from lxml import html
#from urllib import urlencode


def nonempty(x):
    return len(x) != 0


def trimmed(s):
    return s.strip()


def first(s):
    return s[0]


def clean_nulls(v):
    return '' if v is None else v


def scrape_rows(rows):
    return filter(nonempty, [
        filter(nonempty, [
            value.strip().replace(',', '') for value in row.xpath('td/text()')
        ])
        for row in rows if len(row) != 0
    ])


def fetch_summary_page(page=1):
    params = {
        '__EVENTTARGET': 'ctl00$MainContent$grdResults',
        '__EVENTARGUMENT' : 'Page${}'.format(page),
        '__VIEWSTATE': __VIEWSTATE,
        '__VIEWSTATEGENERATOR': '58564CAC',
        '__VIEWSTATEENCRYPTED': '',
        'ctl00$hdnKeepAlive': 'No',
        'ctl00$MainContent$txtSalesFrom': '01/01/2011',
        'ctl00$MainContent$txtSalesTo': '10/30/2017',
        'ctl00$MainContent$txtSalePriceFrom': 350000,
        'ctl00$MainContent$txtSalePriceTo': 1500000,
        'ctl00$MainContent$txtLandFrom': 0.1,
        'ctl00$MainContent$txtLandTo': 2,
        'ctl00$MainContent$RadioButtonList1': 'AC',
        'ctl00$MainContent$txtBldAreaFrom': '900',
        'ctl00$MainContent$txtBldAreaTo': '2000',
        'ctl00$MainContent$cblModels$1': '01',
        'ctl00$MainContent$ddlNbhd': 'All',
        'ctl00$MainContent$cblStyles$0': '01',
        'ctl00$MainContent$cblStyles$1': '02',
        'ctl00$MainContent$cblStyles$2': '03',
        'ctl00$MainContent$cblStyles$3': '04',
        'ctl00$MainContent$cblStyles$4': '05',
        'ctl00$MainContent$cblStyles$5': '06',
        'ctl00$MainContent$cblStyles$6': '07',
        'ctl00$MainContent$cblStyles$7': '08',
        'ctl00$MainContent$cblStyles$8': '10',
        'ctl00$MainContent$cblStyles$9': '100',
        'ctl00$MainContent$cblStyles$10': '11',
        'ctl00$MainContent$cblStyles$11': '12',
        'ctl00$MainContent$cblStyles$12': '13',
        'ctl00$MainContent$cblStyles$13': '14',
        'ctl00$MainContent$cblStyles$14': '16',
        'ctl00$MainContent$cblStyles$15': '17',
        'ctl00$MainContent$cblStyles$16': '18',
        'ctl00$MainContent$cblStyles$17': '19',
        'ctl00$MainContent$cblStyles$18': '25',
        'ctl00$MainContent$cblStyles$19': '26',
        'ctl00$MainContent$cblStyles$20': '27',
        'ctl00$MainContent$cblStyles$21': '29',
        'ctl00$MainContent$cblStyles$22': '30',
        'ctl00$MainContent$cblStyles$23': '31',
        'ctl00$MainContent$cblStyles$24': '36',
        'ctl00$MainContent$cblStyles$25': '39',
        'ctl00$MainContent$cblStyles$26': '41',
        'ctl00$MainContent$cblStyles$27': '48',
        'ctl00$MainContent$cblStyles$28': '54',
        'ctl00$MainContent$cblStyles$29': '55',
        'ctl00$MainContent$cblStyles$30': '56',
        'ctl00$MainContent$cblStyles$31': '60',
        'ctl00$MainContent$cblStyles$32': '61',
        'ctl00$MainContent$cblStyles$33': '66',
        'ctl00$MainContent$cblStyles$34': '71',
        'ctl00$MainContent$cblStyles$35': '77',
        'ctl00$MainContent$cblStyles$36': '86',
        'ctl00$MainContent$cblStyles$37': '94',
        'ctl00$MainContent$cblStyles$38': '97',
        'ctl00$MainContent$cblStyles$39': '99',
        'ctl00$MainContent$hdnMode': 'results',
        'ctl00$MainContent$hdnLotTypeSearch': 'No',
    }
    response = requests.post('http://gis.vgsi.com/concordma/Sales.aspx', params)
    doc = html.fromstring(response.content)
    rows = doc.xpath('//table[caption[normalize-space(text())="Results"]]//tr')
    data = scrape_rows(rows)
    addresses = map(
        first,
        filter(
            nonempty,
            [map(trimmed, row.xpath('td/a/text()')) for row in rows]
        )
    )
    pages = [
        'http://gis.vgsi.com' + hrefs[0]
        for hrefs in filter(nonempty, [row.xpath('td/a/@href') for row in rows])
        if 'Parcel' in hrefs[0]
    ]
    return zip(addresses, pages, *zip(*data))


def collect_summary_data():
    data = []
    last = []
    page = 1
    while True:
        next = fetch_summary_page(page=page)
        if next == last:
            break
        data.extend(next)
        last = next
        page += 1
    return data


def collect_additional_data(row):
    url = row[1]
    response = requests.get(url)
    doc = html.fromstring(response.content)
    appraisals = scrape_rows(
        doc.xpath(
            '//table[caption[normalize-space(text())="Appraisal"]]'
        )[1].xpath('tr')
    )
    assessments = dict((row[0], row[1:]) for row in scrape_rows(
        doc.xpath(
            '//table[caption[normalize-space(text())="Assessment"]]'
        )[1].xpath('tr')
    ))
    apprs = [appraised + assessments[appraised[0]] for appraised in appraisals]
    attr = dict([kvp for kvp in scrape_rows(
        doc.xpath(
            '//table[caption[normalize-space(text())="Building Attributes"]]/tr'
        )
    ) if len(kvp) == 2])
    row = tuple(row) + tuple(map(clean_nulls, (
        attr.get('Stories:'),
        attr.get('Total Rooms:'), 
        attr.get('Total Bedrooms:'), 
        attr.get('Total Bthrms:'), 
        attr.get('Total Half Baths:'), 
    )))
    return [tuple(appraisal) + row for appraisal in apprs]


def main():
    data = collect_summary_data()
    print 'YEAR,APPRAISED IMPROVEMENTS,APPRAISED LAND,APPRAISED TOTAL,\
ASSESSED IMPROVEMENTS,ASSESSED LAND, ASSESSED TOTAL,ADDRESS,URL,SALE DATE,\
SALE PRICE,MODEL,STYLE,LIVING AREA,\
LAND AREA(SF),NBHD,STORIES,ROOMS,BEDROOMS,BATHS,HALF BATHS'
    for d in data:
        for e in collect_additional_data(d):
            print ','.join(e)


__VIEWSTATE = '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'


if __name__ == '__main__':
    main()
