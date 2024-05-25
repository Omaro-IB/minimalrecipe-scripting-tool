import requests
import json
from os import path

import recipe_finder


def get_html(url, min_length=50000):
    """
    Get HTML from any web link
    :param url: the web link; str
    :param min_length: minimum accepted HTML length for using raw request; int
    :return: the HTML markdown; str
    """
    r = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'})

    if len(r.text) < min_length:  # HTML is less than min_length, is probably dynamically loaded by JS
        from get_html_selenium import get_html_selenium
        return get_html_selenium(url)

    return r.text


def get_recipe(html, lookfor='"@type"'):
    """
    Get JSON formatted recipe
    :param html: the HTML code to parse
    :param lookfor: (optional) where to start searching for the JSON object
    :return: recipe JSON object
    """
    # find JSON object {} by starting at the "lookfor"
    j = html.find(lookfor)
    if j == -1:
        return

    # get first '{' by searching backwards
    counter = 1
    while counter > 0:
        j -= 1
        if html[j] == "}":
            counter += 1
        elif html[j] == "{":
            counter -= 1
    start = j

    # get string from first '{' to last '}'
    counter = 1
    while counter > 0:
        j += 1
        if html[j] == "{":
            counter += 1
        elif html[j] == "}":
            counter -= 1

    # create JSON object
    json_recipe = json.loads(html[start:j + 1])
    try:
        typ = json_recipe["@type"]
    except KeyError:
        if lookfor == '"@type":"Recipe"':  # second attempt, give up
            return
        else:
            return get_recipe(html, lookfor='"@type":"Recipe"')  # try again with different lookfor

    if "Recipe" not in typ:  # recursive try, try with next segment of HTML
        return get_recipe(html[j + 1:])
    else:  # successful try
        return json_recipe


def clean_recipe(recipe_json):
    """
    Takes recipe JSON object and returns standardized "cleaned" dictionary
    :param recipe_json: the recipe JSON object
    :return: a standardized dictionary with exactly the following keys: name, articleBody, totalTime, cookTime,
                                                            recipeYield, recipeIngredients, recipeInstructions
    """
    cleaned = {}
    # Dictionary below defines keywords. Structure is keyword (lowercase):refword (refwords MUST be one of below)
    # refwords: name, articleBody, totalTime, cookTime, recipeYield, recipeIngredients, recipeInstructions
    key = {"totaltime": "totalTime", "cooktime": "cookTime", "preptime": "cookTime", "name": "name", "title": "name",
           "article": "articleBody", "body": "articleBody", "description": "articleBody", "yield": "recipeYield",
           "ingredient": "recipeIngredients", "instruction": "recipeInstructions"}

    # Go through all keywords and add to "cleaned" dictionary
    keyword_list = list(key.keys())  # list of all keywords
    for recipeKey in recipe_json:
        for keyword in keyword_list:
            if keyword in recipeKey.lower():  # a keyword matches this JSON entry
                if (key[keyword] == "recipeIngredients") or (key[keyword] == "recipeInstructions"):
                    cleaned[key[keyword]] = recipe_json[recipeKey]  # set to original JSON entry

                elif type(recipe_json[recipeKey]) is list:
                    cleaned[key[keyword]] = recipe_json[recipeKey][0]  # set to first in list only

                elif type(recipe_json[recipeKey]) is dict:  # handle dictionary case (only if key is "text" or "url")
                    if "text" in recipe_json[recipeKey]:
                        cleaned[key[keyword]] = recipe_json[recipeKey]["text"]
                    elif "url" in recipe_json[recipeKey]:
                        cleaned[key[keyword]] = recipe_json[recipeKey]["url"]
                    else:  # unknown key, give up
                        return

                else:
                    cleaned[key[keyword]] = recipe_json[recipeKey]  # set to original JSON entry

                continue

    # Handling strange "recipeInstructions" formatting
    if type(cleaned['recipeInstructions'][0]) is dict:
        cleaned_instructions = []
        for i in cleaned['recipeInstructions']:
            try:
                cleaned_instructions.append(i['text'])
            except KeyError:
                try:
                    t = i["itemListElement"]
                    te = ""
                    for t1 in t:
                        te = te + t1['text'] + "<br><br>"
                    cleaned_instructions.append(te)
                except KeyError:
                    cleaned_instructions.append(i)
        cleaned['recipeInstructions'] = cleaned_instructions
    elif type(cleaned['recipeInstructions'][0]) is str:
        cleaned['recipeInstructions'] = [cleaned['recipeInstructions']]
    elif not (type(cleaned['recipeInstructions']) is list):
        return

    # Handling 2D list for instructions (transform [[x, y, z]] -> [x, y, z])
    if type(cleaned["recipeInstructions"]) is list:
        if len(cleaned["recipeInstructions"]) == 1 and type(cleaned["recipeInstructions"][0]) is list:
            cleaned["recipeInstructions"] = cleaned["recipeInstructions"][0]

    # Ensures instructions and ingredients are present (the two critical components to a recipe)
    if not ("recipeInstructions" in cleaned and "recipeIngredients" in cleaned):
        return

    # Further handling of other keys
    keys = ["name", "articleBody", "cookTime", "totalTime", "recipeYield"]
    for i in keys:
        if (not (i in cleaned)) or (cleaned[i] is None):
            cleaned[i] = ''  # if they do not exist, set it to empty string
        if (i == "cookTime" or i == "totalTime") and cleaned[i][:2] == "PT":
            cleaned[i] = cleaned[i][2:]  # remove "PT" in any times

    return cleaned


def create_minimized_html(cleaned_recipe):
    """
    Takes standardized dictionary and returns HTML, requires HTML file template in "recipe/single-recipe-template.html"
    :param cleaned_recipe: the standardized recipe dictionary
    :return: the final HTML markdown; list
    """
    # Get template lines
    working_path = path.dirname(path.abspath(__file__))
    with open(r"{}\recipe\single-recipe-template.html".format(working_path)) as f:
        lines = f.readlines()
    final_lines = []

    # Replace placeholders with values in cleaned recipe
    for line in lines:
        if "(name)" in line:  # name
            final_lines.append(line.replace("(name)", str(cleaned_recipe["name"])))
        elif "(articleBody)" in line:  # body
            final_lines.append(line.replace("(articleBody)", str(cleaned_recipe["articleBody"])))
        elif "(cookTime)" in line:  # cook time
            final_lines.append(line.replace("(cookTime)", str(cleaned_recipe["cookTime"])))
        elif "(totalTime)" in line:  # total time
            final_lines.append(line.replace("(totalTime)", str(cleaned_recipe["totalTime"])))
        elif "(recipeYield)" in line:  # yield
            final_lines.append(line.replace("(recipeYield)", str(cleaned_recipe["recipeYield"])))
        elif "<!-- start instructions -->" in line:  # instructions (loop through list)
            for i in range(len(cleaned_recipe["recipeInstructions"])):
                final_lines.append('<div class="single-instruction"><header>')
                final_lines.append('<p>step {}</p>'.format(i+1))
                final_lines.append('<div></div></header><p>{}</p></div>'.format(cleaned_recipe["recipeInstructions"][i]))
        elif "<!-- start ingredients -->" in line:  # ingredients (loop through list)
            for i in cleaned_recipe["recipeIngredients"]:
                final_lines.append('<p class="single-ingredient">{}</p>'.format(i))
        else:  # non-placeholder line
            final_lines.append(line)

    return final_lines


def url_to_html(url):
    """
    Uses above functions to streamline process from URL -> final HTML
    :param url: The web link to the recipe
    :return: A two-tuple (name, HTML) -- the name of the dish and the HTML markdown of the recipe
            Exceptions: 0 = could not find a recipe in the webpage, -1 = could not parse the recipe,
                                                                            -2 = could not find dish name (invalid URL)
    """
    try:
        html = get_html(url)
    except (requests.exceptions.InvalidURL, requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        return -2
    recipe = get_recipe(html, lookfor='"@type":"Recipe"')  # Step 1: Get HTML code and extract JSON

    if recipe is None:  # Step 1: try again with different lookfor
        recipe = get_recipe(get_html(url))
    if recipe is None:  # Step 1: failed to find recipe, give up
        return 0

    cleaned_recipe = clean_recipe(recipe)  # Step 2: clean recipe JSON into standardized dictionary
    if cleaned_recipe is None:  # Step 2: failed to parse recipe, give up
        return -1

    minimized_html = create_minimized_html(cleaned_recipe)  # Step 3: convert standardized dictionary to HTML markdown

    # Get name from dictionary and ensure no prohibited characters

    name = str(cleaned_recipe["name"])
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace("*", "_")
    name = name.replace(":", "_")
    name = name.replace("?", "_")
    name = name.replace('"', "_")
    name = name.replace("<", "_")
    name = name.replace(">", "_")
    name = name.replace("|", "_")

    return name, minimized_html


def name_to_html(name):
    """
    Uses recipe_finder.py to get HTML from the name
    :param name: the dish name; String
    :return: A two-tuple (name, HTML) -- the name of the dish and the HTML markdown of the recipe
            Exceptions: 0 = could not find a recipe in the webpage, -1 = could not parse the recipe,
                                                                                        -2 = could not find dish name
    """
    lowest_levenshtein = 999999
    best_val = None
    best_link = None
    error_code = -2

    # List of functions to use to find links
    function_list = (recipe_finder.get_recipetineats_link, recipe_finder.get_allrecipes_link,
                     recipe_finder.get_nyt_link, recipe_finder.get_seriouseats_link)
    # List of websites (should correspond 1:1 with above function list) - only used for error messaging
    website_list = ("www.recipetineats.com", "www.allrecipes.com", "cooking.nytimes.com", "www.seriouseats.com")

    for func in range(len(function_list)):  # try all link from name functions
        link = function_list[func](name)
        if link is None:  # link not found
            error_code = -2
            print(f'Checked website "{website_list[func]}" with no results')

        else:
            val = url_to_html(link)
            if val == 0 or val == -1 or val == -2:  # found link but issue finding or parsing recipe
                error_code = val
                print(f'Checked link "{link[:80]}" with error code {error_code}')
            else:  # everything successful
                current_levenshtein = recipe_finder.levenshtein(name, val[0])
                print(f'Checked link "{link[:80]}" successfully, similarity score = {current_levenshtein} '
                      f'(smaller score is better)')
                if current_levenshtein < lowest_levenshtein:  # if it is closer to user input
                    lowest_levenshtein = current_levenshtein
                    best_val = val
                    best_link = link

    if best_val:  # at least one successful attempt
        # shorten url to domain name for displaying in file name
        start = best_link.find("//")
        end = best_link[start + 2::].find("/")
        new_name = best_val[0] + f" (from {best_link[start+2:start+end+2]})"  # add website source to file name
        return new_name, best_val[1]
    else:  # return latest error code
        return error_code
