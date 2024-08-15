# EXTERNAL LIBRARIES AND FUNCTIONS
from generate_html import url_to_html
from generate_html import name_to_html
from generate_html import create_minimized_html
import sys
from webbrowser import open_new
from urllib.parse import unquote


# URL MANIPULATION FUNCTIONS
def google_url_cleaner(google_url):
    """
    Takes a Google redirect URL and parses into original link
    :param google_url: the google.com/url? link
    :return: original URL; str
    """
    url1 = google_url[google_url.find("url")::]
    url2 = url1[url1.find("=")+1::]
    url3 = url2[:url2.find("&")]
    return unquote(url3)


# MAIN
def main(args):
    """
    Main execution of program, should take arguments from console (excluding path argument 0)
    :param args: list of arguments; [Link or Name of dish / "manual", Options]
    :return: None
    """
    from os import getcwd
    from os import path
    recipes_path = getcwd()  # recipe storage directory

    # ARGUMENT HANDLING
    if len(args) == 0:  # User entered "?" or no arguments
        print("Usage:\n  recipe.py <command> [options]")
        print("\nCommands:\n  dish name: finds the recipe based on the name of the dish\n  "
              "Web URL: extracts recipe from given (full) URL\n  "
              "manual: enters manual mode, asks for recipe")
        print("\nOptions:\n  --open: automatically open the recipe in your web browser")
        return

    if args[-1] == "--open":  # User wants to open recipe after creation
        entered_dish_name = " ".join(args[:-1])
        arg = "%20".join(args[:-1])
        open_recipe = True  # set open recipe flag

    else:  # no options given
        entered_dish_name = " ".join(args)
        arg = "%20".join(args)
        open_recipe = False  # unset open recipe flag

    if arg.upper() == "MANUAL":  # manual recipe creation
        name_ = input("Enter name of dish: ")
        while {"/", "\\", "*", ":", "?", '"', "<", ">", "|"}.intersection(name_):  # ensure no forbidden characters
            name_ = input("Forbidden character, enter name: ")

        cleaned = {"name": name_, "articleBody": input("Enter a description of the dish: "),
                   "recipeYield": input("Enter the serving size/yield of the recipe: "),
                   "cookTime": input("Enter cook time: "), "totalTime": input("Enter total time: "),
                   "recipeIngredients": input("Enter ingredients (; seperated): ").split(";"),
                   "recipeInstructions": input("Enter instructions (; seperated): ").split(";")}
        full_path = path.join(recipes_path, cleaned["name"] + ".html")
        with open(full_path, "w+") as f:
            f.writelines(create_minimized_html(cleaned))  # create minimized html
        exit()

    # URL HANDLING (stored in "url", url = None if getting from dish name)
    if "http" in arg:
        url = arg  # store in "url"
        if "www.google.com" in arg:  # handle google redirect URL
            url = google_url_cleaner(url)
    else:  # user inputted dish name, get URL from name
        url = None

    # EXPORTING TO HTML USING "generate_html.py"
    try:
        if url is None:
            val = name_to_html(entered_dish_name)  # gets (file name, HTML) from dish name
        else:
            val = url_to_html(url)  # gets (file name, HTML) from url
    except Exception as e:  # unhandled exception
        print("An unexpected error occurred while retrieving page")
        print(e)
        exit()

    if val == 0:  # error code 0: find recipe in webpage error
        print("We could not find a recipe there")
        exit()
    elif val == -1:  # error code -1: parsing recipe error
        print("We could not parse the recipe")
        exit()
    elif val == -2:  # error code -2: dish name error
        print('We could not find the dish "{}"'.format(entered_dish_name))
    else:  # no unhandled or handled errors
        name, data = val
        full_path = path.join(recipes_path, name + ".html")
        while path.isfile(full_path):  # ensure no file override
            name = name + " (copy)"
            full_path = path.join(recipes_path, name + ".html")
        with open(full_path, "w+", encoding="utf-16") as f:  # finally, write the HTML data
            f.writelines(data)
            if open_recipe:  # open file if flag is set
                open_new("file://{}".format(full_path))
            print("Saved recipe to {}".format(full_path))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as er:
        print("Unknown error (fatal)")
        print(er)
