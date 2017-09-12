# Populate Emoji Database

Code to populate a mysql database with emoji information, including
* codepoints
* emoji characters
* emoji_codepoint sequences
* platforms
* platform versions
* emoji renderings

## DATABASE SETUP
Use the scripts in the database folder to set up the database
First, create a database (if not already created) called emojistudy_db
Then, while in the database folder,

```
> source setup_db.sql
```

Or, you can individually reset the emoji or rendering tables using

```
> source create_emoji.sql
> source create_renderings.sql
```

### Local Config
Once the database is set up, you need to create a local configuration to access it
Create a file called local_config.py with the following config dictionary (and fill in your credentials)

```
db_config = {'user':'',
             'host':'localhost',
             'password':'',
             'database':'emojistudy_db'}
```

If needed, refer to the GroupLens Central [Database Management document](https://docs.google.com/a/umn.edu/document/d/1P3_oWjeGX3qMvay1YAtUsAV8mgcIowyx-5O7_0wzrBA/edit?usp=sharing) for information about creating/adding users with database access, etc.


## EMOJI DATA
This code relies on keeping the emoji_data.py file up-to-date:
* PLATFORMS
  - This list is the list of platforms you would like to support in your database
* PLATFORM_VERSIONS
  - This list is the list of platform versions you would like to support in your database
  - This list is created by taking versions from Emojipedia. In general, Emojipedia's naming scheme matches its urls (url = lowercase version name with spaces replaced by '-'). The list of platform versions must be formatted as the version name that follows this url heuristic. If the version name and url do not follow this heuristic, put the version name in the list that suffices the heuristic for the url conversion, then add this version name with the actual version name in the PLATFORM_VERSION_URL_MISMATCH dictionary.
  - This list must be ordered such that all versions for a given platform are consecutive, and in order from most recent to the oldest version
* Unicode_Emoji_Data
  - This class contains lists for
    * EMOJI_MODIFIERS
    * EMOJI_MODIFIER_BASES
    * EMOJI_COMPONENTS
    * EMOJI
  - To make these lists, I converted the associated js lists from https://github.com/mathiasbynens/unicode-tr51 whose codebase parses the emoji data lists given by the Unicode and generates these lists
  - Need to check this repository/the Unidoce emoji data lists to see if you need to update these lists (ex. when they come out with new emoji versions)


## TO RUN
Once the database is set up, use `populatedb_emoji.py` to populate the codepoints, emoji characters, and emoji codepoint tables, then `populatedb_renderings.py` to populate the platforms, platform versions, and renderings tables

Note: You may have to

```
> unset http_proxy
> unset https_proxy
```

in the command line before scraping, perhaps if getting 'Unexpected EOF' errors


## SQL OUTPUT
The python populate scripts create sql scripts to mimic the database insertions/updates that were performed. Therefore,these scripts (`insert_emoji.sql` and `insert_renderings.sql`) can be used to populate the database without re-running the python scripts (re-scraping and collecting data) (much faster).


## EMOJIPEDIA CODE CREDIT
The files in the emojipedia fodler (emoji.py and emojipedia.py) are slightly-modified copies from the [python-emojipedia package](https://github.com/bcongdon/python-emojipedia) (Copyright (c) 2016 Ben Congdon)
I needed to make my own copies of these files rather than simply install and use the emojipedia python package (which I was doing, originally) because I ran into too many errors related to network noise.

In my own copies, I use request sessions with adapters configured for retries to handle network noise. I also added a property for the emoji's url extension (which we needed for identifying emoji in our rendering scraping algorithm from the platform version pages).
At this point in time, these are the only difference between my copies and their code base (9/12/17)


