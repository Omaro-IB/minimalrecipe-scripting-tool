import requests


def levenshtein(str_a, str_b, caps=False):
    """
    Calculates similarity of two strings using their Levenshtein distance
    :param str_a: the first string; String
    :param str_b: the second string; String
    :param caps: case-sensitive?; Boolean; default = False
    :return: the Levenshtein distance; Float
    """
    if not caps:
        return levenshtein(str_a, str_b, caps=True)

    m = len(str_a)
    n = len(str_b)
    d = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        d[i][0] = i

    for j in range(1, n + 1):
        d[0][j] = j

    for j in range(1, n + 1):
        for i in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                cost = 0
            else:
                cost = 1
            d[i][j] = min(d[i - 1][j] + 1,  # deletion
                          d[i][j - 1] + 1,  # insertion
                          d[i - 1][j - 1] + cost)  # substitution

    return d[m][n]


# LINK FROM DISH NAME FUNCTIONS - TAKE DISH NAME AND RETURN LINK, IF NO LINK FOUND THEN RETURN NONE
def get_nyt_link(dish):
    """
    Takes a dish name and returns NYT Cooking recipe link
    :param dish: the dish name; str
    :return: recipe link; str, if no results return None
    """
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'

    url_nyt = "https://cooking.nytimes.com/search?q={}".format(dish)
    r = requests.get(url_nyt, headers={'User-Agent': agent})
    html = r.text
    start = html.find('href="/recipes')
    i = start
    while html[i] != ">":
        i += 1

    url = "https://cooking.nytimes.com"+html[start+6:i-1]
    if url[27] != "/":  # no results from NYT
        return None
    else:
        return url


def get_allrecipes_link(dish):
    """
    Takes a dish name and returns All Recipes Cooking recipe link
    :param dish: the dish name; str
    :return: recipe link; str, if no results return None
    """
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'

    url_allr = "https://www.allrecipes.com/search?q={}".format(dish)
    r = requests.get(url_allr, headers={'User-Agent': agent})

    html = r.text
    url = "gallery"
    i = 0

    while "gallery" in url:
        html = html[i + 5:]
        start = html.find('data-tax-levels href="')
        i = start
        x = 0
        while x < 2:
            if html[i] == '"':
                x += 1
            i += 1
        url = html[start+22:i-1]

    if "/" not in url:  # no results from NYT
        return None
    else:
        return url


def get_recipetineats_link(dish):
    """
    Takes a dish name and returns Recipe Tin Eats recipe link
    :param dish: the dish name; str
    :return: recipe link; str, if no results return None
    """
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'

    url = "https://www.recipetineats.com/?s={}".format(dish)
    r = requests.get(url, headers={'User-Agent': agent})

    html = r.text
    html = html[html.find("Search Results for")+50:]
    html = html[html.find("Search Results for"):]
    html = html[html.find("href="):]
    html = html[6:html.find('/"')]
    if html == "https://www.recipetineats.com/nagi-recipetin-eats":
        return None
    else:
        return html


def get_seriouseats_link(dish):
    """
    Takes a dish name and returns Serious Eats recipe link
    :param dish: the dish name; str
    :return: recipe link; str, if no results return None
    """
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'

    url = "https://www.seriouseats.com/search?q={}".format(dish)
    r = requests.get(url, headers={'User-Agent': agent})

    html = r.text
    html = html[html.find('href="https://www.seriouseats.com/about-us-5120006#toc-contact-us"')+50:]
    html = html[html.find("href")+6:]
    html = html[:html.find('">')]
    return html
