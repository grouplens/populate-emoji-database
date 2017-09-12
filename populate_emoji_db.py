import dateparser
import mysql.connector
from local_config import db_config
from emojipedia import Emojipedia,EMOJI_CATEGORIES
from emoji_data import Unicode_Emoji_Data,PLATFORM_VERSIONS,PLATFORM_VERSION_URL_MISMATCH

use_db = True
skip_emoji = False
skip_renderings = False

if use_db:
    # Connect to the database
    cnx = mysql.connector.connect(user=db_config['user'],
                                  host=db_config['host'],
                                  password=db_config['password'],
                                  database=db_config['database'])
    cursor = cnx.cursor()

# Write all data definition queries to a file to be able to recreate the database without scraping
with open('insert_emoji_alldata.sql','w', encoding='utf-8') as db_file:
    if use_db:
        print('USE emojistudy_db;',file=db_file)
        print(file=db_file)


    print("Inserting PLATFORMS")
    # -------- PLATFORMS --------
    our_platforms = ['apple','google','htc','lg','microsoft','samsung','twitter']
    insert_platform_query = ("INSERT INTO platforms "
                             "(platform_id,platform_name) "
                             "VALUES (%(id)s, %(name)s);")
    platform_dict = {}
    platform_index = 1
    for platform in our_platforms:
        cur_dict = {'id':platform_index,'name':platform}
        platform_dict[platform] = cur_dict
        if use_db:
            cursor.execute(insert_platform_query,cur_dict)
            print(cursor.statement,file=db_file)
        platform_index += 1

    if use_db:
        print(file=db_file)
        cnx.commit()
    print("- Completed -")
    print()


    # -------- PLATFORM VERSIONS --------
    print("Inserting PLATFORM VERSIONS")
    insert_platform_version_query = ("INSERT INTO platform_versions "
                                     "(platform_version_id,platform_id,version_name,emojipedia_url_ext,post_version_id) "
                                     "VALUES (%(id)s, %(platform_id)s, %(name)s, %(url)s, %(post_version_id)s);")
    platform_version_list = []
    last_looked_at_platform = None
    num_versions = len(PLATFORM_VERSIONS)
    platform_version_index = 1
    for i in range(0,num_versions):
        version = PLATFORM_VERSIONS[i]
        version_split = version.split(' ')

        platform = version_split[0].lower()
        version_name = ' '.join(version_split[1:])
        if version in PLATFORM_VERSION_URL_MISMATCH:
            version_name = PLATFORM_VERSION_URL_MISMATCH[version]
        version_url_ext = ('-'.join(version_split[1:])).lower()

        # The list is ordered from most recent to least recent
        # so if the last looked at platform in the list is for the same platform,
        # then the last looked at platform is the "post version" of the version
        # we are currently looking at
        post_platform_index = None
        if platform == last_looked_at_platform:
            post_platform_index = platform_version_index - 1
        last_looked_at_platform = platform

        # likewise, the next version to look at in the list is the "previous version"
        # of the version we are currently looking at,
        # unless it is for a different platform, in which the current version is the oldest version
        # or unless the version we are currently looking at is the last version in the list,
        # also making it the oldest version
        prev_platform_index = platform_version_index + 1
        if (platform_version_index < num_versions-1 and \
            not PLATFORM_VERSIONS[i+1].startswith(version_split[0])) \
           or (platform_version_index == num_versions):
            prev_platform_index = None

        cur_dict = {'id':platform_version_index,
                    'platform':platform,
                    'platform_id':platform_dict[platform]['id'],
                    'name':version_name,
                    'url':platform+'/'+version_url_ext,
                    'prev_version_id':prev_platform_index,
                    'post_version_id':post_platform_index}
        platform_version_list.append(cur_dict)
        if use_db:
            cursor.execute(insert_platform_version_query,cur_dict)
            print(cursor.statement,file=db_file)

        platform_version_index += 1

    if use_db:
        print(file=db_file)
        cnx.commit()
    print("- Completed -")
    print()


    # -------- CODEPOINTS --------
    print("Inserting CODEPOINTS")
    insert_codepoint_query = ("INSERT INTO codepoints "
                              "(codepoint_id,codepoint,isComponent,isModifier,isModifierBase) "
                              "VALUES (%(id)s, %(codepoint)s, %(isComponent)s, %(isModifier)s, %(isModifierBase)s);")
    codepoint_dict = {}
    codepoint_index = 1
    for codepoint in Unicode_Emoji_Data.EMOJI:
        isComponent = codepoint in Unicode_Emoji_Data.EMOJI_COMPONENTS
        isModifier = codepoint in Unicode_Emoji_Data.EMOJI_MODIFIERS
        isModifierBase = codepoint in Unicode_Emoji_Data.EMOJI_MODIFIER_BASES
        cur_dict = {'id':codepoint_index,
                    'codepoint':codepoint,
                    'isComponent':isComponent,
                    'isModifier':isModifier,
                    'isModifierBase':isModifierBase}
        codepoint_dict[codepoint] = cur_dict
        if use_db:
            cursor.execute(insert_codepoint_query,cur_dict)
            print(cursor.statement,file=db_file)
        codepoint_index += 1
    for codepoint in Unicode_Emoji_Data.EMOJI_COMPONENTS:
        if codepoint not in codepoint_dict:
            isModifier = codepoint in Unicode_Emoji_Data.EMOJI_MODIFIERS
            isModifierBase = codepoint in Unicode_Emoji_Data.EMOJI_MODIFIER_BASES
            cur_dict = {'id':codepoint_index,
                        'codepoint':codepoint,
                        'isComponent':True,
                        'isModifier':isModifier,
                        'isModifierBase':isModifierBase}
            codepoint_dict[codepoint] = cur_dict
            if use_db:
                cursor.execute(insert_codepoint_query,cur_dict)
                print(cursor.statement,file=db_file)
            codepoint_index += 1

    if use_db:
        print(file=db_file)
        cnx.commit()
    print("- Completed -")
    print()


    # -------- EMOJI & EMOJI CODEPOINTS --------
    if skip_emoji:
        print('Skipping EMOJI')
        print()
    else:
        print('Creating emoji category dictionary')
        # Create Emojipedia emoji category dictionary
        emoji_category_dict = {}
        category_count = {}
        for category in EMOJI_CATEGORIES:
            category_emoji = Emojipedia.category(category)
            #print(category,": ",len(category_emoji))
            category_count[category] = {'count':0, 'total':len(category_emoji)}
            for emoji in category_emoji:
                emoji_category_dict[emoji.title] = category
        print('- Completed -')
        print()


        print('Inserting EMOJI & EMOJI CODEPOINTS')
        insert_emoji_query = ("INSERT INTO emoji "
                              "(emoji_id,emoji_name,emojipedia_url_ext,emojipedia_category,codepoint_string,num_codepoints,hasComponent,hasModifier,hasModifierBase,appearance_differs_flag,unicode_not_recommended) "
                              "VALUES (%(id)s, %(name)s, %(url)s, %(category)s, %(codepoint_string)s, %(num_codepoints)s, %(hasComponent)s, %(hasModifier)s, %(hasModifierBase)s, %(appearance_differs)s, %(not_recommended)s);")

        insert_emoji_codepoint_query = ("INSERT INTO emoji_codepoints "
                                        "(emoji_codepoint_id,emoji_id,codepoint_id,sequence_index) "
                                        "VALUES (%(id)s, %(emoji_id)s, %(codepoint_id)s, %(sequence_index)s);")

        # Get all the emoji
        emojis = Emojipedia.all()
        #print(len(emojis))
        emoji_counts_dict = {}
        emoji_index = 1
        emoji_codepoint_index = 1
        for emoji in emojis:
            # if emoji_index > 20:
            #     break

            hasComponent = False
            hasModifier = False
            hasModifierBase = False
            emoji_codepoint_list = []
            sequence = 1
            is_emoji = True
            for codepoint_U in emoji.codepoints:
                codepoint = codepoint_U[2:] # codepoints are pre-pended with U+
                cur_codepoint_dict = codepoint_dict.get(codepoint,None)
                if cur_codepoint_dict is None:
                    is_emoji = False
                    break
                hasComponent = hasComponent or cur_codepoint_dict['isComponent']
                hasModifier = hasModifier or cur_codepoint_dict['isModifier']
                hasModifierBase = hasModifierBase or cur_codepoint_dict['isModifierBase']

                emoji_codepoint_list.append({'id':emoji_codepoint_index,
                                             'emoji_id':emoji_index,
                                             'codepoint_id':cur_codepoint_dict['id'],
                                             'sequence_index':sequence})
                emoji_codepoint_index += 1
                sequence += 1
            if not is_emoji:
                print('skipping {0}, not an emoji'.format(emoji.title))
                print('-- skipping {0}, not an emoji'.format(emoji.title),file=db_file)
                continue
            
            url = emoji.url.strip('/')

            emoji_category = None
            if emoji.title in emoji_category_dict:
                emoji_category = emoji_category_dict[emoji.title]
                category_count[emoji_category]['count'] += 1
            
            # Codepoint String = straight string of codepoints: U+###U+#### (to extract, .split('U+'))
            codepoint_string = ''.join(emoji.codepoints)

            # Description flags for appearance differing across platforms or not being recommended by the Unicode
            description = emoji.description
            appearance_differs = True if "Appearance differs greatly cross-platform." in description else False
            not_recommended = True if "has not been recommended by Unicode." in description else False
            if not not_recommended:
                not_recommended = True if "has not been Recommended For General Interchange (RGI) by Unicode." in description else False

            cur_dict = {'id':emoji_index,
                        'name':emoji.title,
                        'url':url,
                        'category':emoji_category,
                        #'raw_character':emoji.character,
                        'codepoint_string':codepoint_string,
                        'num_codepoints':len(emoji.codepoints),
                        'hasComponent':hasComponent,
                        'hasModifier':hasModifier,
                        'hasModifierBase':hasModifierBase,
                        'appearance_differs':appearance_differs,
                        'not_recommended':not_recommended}
            emoji_counts_dict[url] = {'id':emoji_index,
                                      'platforms':[],
                                      'num_renderings':0,
                                      'num_changed_renderings':0}
            if use_db:
                cursor.execute(insert_emoji_query,cur_dict)
                print(cursor.statement,file=db_file)
                cursor.executemany(insert_emoji_codepoint_query,emoji_codepoint_list)
                print(cursor.statement,file=db_file)
                print(file=db_file)
            if emoji_index % 50 == 0:
                print('completed 50 emoji ({0} total so far)'.format(emoji_index))
            emoji_index += 1

        if use_db:
            cnx.commit()
        print('- Completed - ({0} emoji inserted)'.format(emoji_index-1))
        print()

        for category in EMOJI_CATEGORIES:
            print("for category ",category,", found: ",category_count[category]['count']," out of ",category_count[category]['total'])
        print()

    # -------- RENDERINGS & rest of PLATFORM VERSIONS --------
    if skip_renderings:
        print('Skipping RENDERINGS & rest of PLATFORM VERSIONS')
        print()
    else:
        print('Inserting RENDERINGS & Updating rest of PLATFORM VERSIONS')
        insert_rendering_query = ("INSERT INTO renderings "
                                  "(rendering_id,emoji_id,platform_version_id,display_url,isNew,isChanged) "
                                  "VALUES (%(id)s, %(emoji_id)s, %(platform_version_id)s, %(display_url)s, %(isNew)s, %(isChanged)s);")

        update_platform_version_query = ("UPDATE platform_versions SET "
                                         "prev_version_id = %(prev_version_id)s, "
                                         "release_date = %(release_date)s, "
                                         "num_emoji = %(num_emoji)s, "
                                         "num_changed_emoji = %(num_changed)s, "
                                         "num_new_emoji = %(num_new)s, "
                                         "num_removed_emoji = %(num_removed)s "
                                         "WHERE platform_version_id = %(id)s;")
        rendering_index = 1
        for platform_version in platform_version_list:
            print('renderings and updating {0}'.format(platform_version['name']))
            # First, build lists of changed emoji and new emoji
            # get changed emoji
            soup = Emojipedia._get_page(platform_version['url']+'/changed')
            emoji_list = soup.find('ul', {'class': 'emoji-grid'})
            changed_emoji_list = []
            for emoji_entry in emoji_list.find_all('li'):
                # extract emoji url and then find associated emoji
                emoji_url = emoji_entry.findNext('a')['href'].rstrip('/')
                emoji_url_ext = emoji_url[(emoji_url.rindex('/')+1):]
                cur_dict = emoji_counts_dict.get(emoji_url_ext,None)
                if cur_dict:
                    cur_dict['num_changed_renderings'] += 1
                else:
                    print('found changed rendering not in emoji list: {0}'.format(emoji_url_ext))
                changed_emoji_list.append(emoji_url_ext)
            platform_version['num_changed'] = len(changed_emoji_list)

            # get new emoji
            soup = Emojipedia._get_page(platform_version['url']+'/new')
            emoji_list = soup.find('ul', {'class': 'emoji-grid'})
            new_emoji_list = []
            for emoji_entry in emoji_list.find_all('li'):
                # extract emoji url and then find associated emoji
                emoji_url = emoji_entry.findNext('a')['href'].rstrip('/')
                emoji_url_ext = emoji_url[(emoji_url.rindex('/')+1):]
                new_emoji_list.append(emoji_url_ext)
            platform_version['num_new'] = len(new_emoji_list)

            # get removed emoji
            soup = Emojipedia._get_page(platform_version['url']+'/removed')
            emoji_list = soup.find('ul', {'class': 'emoji-grid'})
            platform_version['num_removed'] = len(emoji_list.find_all('li'))

            # Now, get the version page and get all the renderings
            soup = Emojipedia._get_page(platform_version['url'])
            emoji_list = soup.find('ul', {'class': 'emoji-grid'})
            num_emoji = 0
            for emoji_entry in emoji_list.find_all('li'):
                # extract emoji url and then find associated emoji
                emoji_url = emoji_entry.findNext('a')['href'].rstrip('/')
                emoji_url_ext = emoji_url[(emoji_url.rindex('/')+1):]

                # update emoji counts
                counts_dict = emoji_counts_dict.get(emoji_url_ext,None)
                if counts_dict:
                    emoji_id = counts_dict['id']

                    counts_dict['num_renderings'] += 1
                    if platform_version['platform'] not in counts_dict['platforms']:
                        counts_dict['platforms'].append(platform_version['platform'])

                    # get image display url from the img src
                    img_src = emoji_entry.findNext('img')['src']
                    if img_src.endswith('lazy.svg'):
                        img_src = emoji_entry.findNext('img')['data-src']

                    isNew = emoji_url_ext in new_emoji_list
                    isChanged = emoji_url_ext in changed_emoji_list

                    # create the rendering, map by platform version id and emoji id
                    rendering_dict = {'id':rendering_index,
                                      'emoji_id':emoji_id,
                                      'platform_version_id':platform_version['id'],
                                      'display_url':img_src,
                                      'isNew':isNew,
                                      'isChanged':isChanged}
                    if use_db and not skip_emoji:
                        cursor.execute(insert_rendering_query,rendering_dict)
                        print(cursor.statement,file=db_file)

                    rendering_index += 1
                else:
                    print('found rendering not in emoji list: {0}'.format(emoji_url_ext))

                num_emoji += 1
                # if num_emoji > 5:
                #     break

            # Update platform version
            platform_version['num_emoji'] = num_emoji
            release_date_text = soup.find('div', {'class': 'content'}).findNext('ul').findNext('li').findNext('li').findNext('li').text[14:]
            release_date = dateparser.parse(release_date_text)
            platform_version['release_date'] = release_date.date()
            if use_db:
                cursor.execute(update_platform_version_query,platform_version)
                print(cursor.statement,file=db_file)

        if use_db:
            print(file=db_file)
            cnx.commit()
        print('- Completed -')
        print()


    # -------- rest of EMOJI --------
    if use_db:
        print('Updating EMOJI counts')
        update_emoji_query = ("UPDATE emoji SET "
                              "num_platforms_support = %(num_platforms)s, "
                              "num_changed_renderings = %(num_changed_renderings)s, "
                              "num_renderings = %(num_renderings)s "
                              "WHERE emoji_id = %(id)s;")
        for url,counts in emoji_counts_dict:
            plat_list = counts.pop('platforms')
            counts['num_platforms'] = len(plat_list)
            cursor.execute(update_emoji_query,counts)
            print(cursor.statement,file=db_file)

        cnx.commit()
        print('- Completed -')
        cnx.close()

        print(file=db_file)
        print('COMMIT;',file=db_file)