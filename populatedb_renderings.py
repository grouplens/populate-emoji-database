import dateparser
import mysql.connector
from local_config import db_config
from emojipedia.emojipedia import Emojipedia,Emoji
from emoji_data import PLATFORMS,PLATFORM_VERSIONS,PLATFORM_VERSION_URL_MISMATCH

# Connect to the database
cnx = mysql.connector.connect(user=db_config['user'],
                              host=db_config['host'],
                              password=db_config['password'],
                              database=db_config['database'])
cursor = cnx.cursor()

# Write all data definition queries to a file to be able to recreate the database without scraping
with open('database/data/insert_renderings.sql','w', encoding='utf-8') as db_file:
    print('USE emojistudy_db;',file=db_file)
    print(file=db_file)

    print("Inserting PLATFORMS")
    # -------- PLATFORMS --------
    insert_platform_query = ("INSERT INTO platforms "
                             "(platform_id,platform_name,platform_display_name) "
                             "VALUES (%(id)s, %(name)s, %(display_name)s);")
    platform_dict = {}
    platform_index = 1
    for (platform,platform_display_name) in PLATFORMS:
        cur_dict = {'id':platform_index,'name':platform,'display_name':platform_display_name}
        platform_dict[platform] = cur_dict
        cursor.execute(insert_platform_query,cur_dict)
        print(cursor.statement,file=db_file)
        platform_index += 1

    print(file=db_file)
    cnx.commit()
    print("- Completed -")
    print()


    # -------- PLATFORM VERSIONS --------
    print("Inserting PLATFORM VERSIONS")
    insert_platform_version_query = ("INSERT INTO platform_versions "
                                     "(platform_version_id,platform_id,version_name,version_display_name,in_use,emojipedia_url_ext,post_version_id) "
                                     "VALUES (%(id)s, %(platform_id)s, %(name)s, %(display_name)s, %(in_use)s, %(url)s, %(post_version_id)s);")
    platform_version_list = []
    last_looked_at_platform = None
    num_versions = len(PLATFORM_VERSIONS)
    platform_version_index = 1
    for i in range(0,num_versions):
        version,display_name,in_use = PLATFORM_VERSIONS[i]
        version_split = version.split(' ')

        platform = version_split[0].lower()
        version_name = ' '.join(version_split[1:])
        if version in PLATFORM_VERSION_URL_MISMATCH:
            version_name = ' '.join(PLATFORM_VERSION_URL_MISMATCH[version].split(' ')[1:])
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
            not PLATFORM_VERSIONS[i+1][0].startswith(version_split[0])) \
           or (platform_version_index == num_versions):
            prev_platform_index = None

        cur_dict = {'id':platform_version_index,
                    'platform':platform,
                    'platform_id':platform_dict[platform]['id'],
                    'name':version_name,
                    'display_name':display_name,
                    'in_use':in_use,
                    'url':platform+'/'+version_url_ext,
                    'prev_version_id':prev_platform_index,
                    'post_version_id':post_platform_index}
        platform_version_list.append(cur_dict)
        cursor.execute(insert_platform_version_query,cur_dict)
        print(cursor.statement,file=db_file)

        platform_version_index += 1

    print(file=db_file)
    cnx.commit()
    print("- Completed -")
    print()


    # -------- POPULATE EMOJI DICTIONARY FROM DATABASE
    print("Getting EMOJI from database")
    emoji_counts_dict = {}
    emoji_dict_query = "SELECT emoji_id,emojipedia_url_ext FROM emoji ORDER BY emoji_id;"
    cursor.execute(emoji_dict_query)
    emoji_index = None
    for id,url in cursor:
        emoji_index = id
        emoji_counts_dict[url] = {'id':id,
                                  'platforms':[],
                                  'num_renderings':0,
                                  'num_changed_renderings':0}
    emoji_index += 1
    print("Next inserted emoji at: {0}".format(emoji_index))
    print("- Completed -")
    print()


    # -------- POPULATE CODE POINT DICTIONARY FROM DATABASE
    print("Getting CODE POINTS from database")
    codepoint_dict = {}
    codepoint_dict_query = "SELECT codepoint_id,codepoint,isComponent,isModifier,isModifierBase FROM codepoints ORDER BY codepoint_id;"
    cursor.execute(codepoint_dict_query)
    for id,codepoint,isComponent,isModifier,isModifierBase in cursor:
        cur_dict = {'id':id,
                    'codepoint':codepoint,
                    'isComponent':True,
                    'isModifier':isModifier,
                    'isModifierBase':isModifierBase}
        codepoint_dict[codepoint] = cur_dict
    emoji_codepoint_index_query = "SELECT MAX(emoji_codepoint_id)+1 FROM emoji_codepoints;"
    cursor.execute(emoji_codepoint_index_query)
    emoji_codepoint_index = cursor.fetchone()[0]
    print("Next inserted emoji codepoint at: {0}".format(emoji_codepoint_index))
    print("- Completed -")
    print()


    # -------- RENDERINGS & rest of PLATFORM VERSIONS --------
    print('Inserting RENDERINGS & Updating rest of PLATFORM VERSIONS')
    insert_rendering_query = ("INSERT INTO renderings "
                              "(rendering_id,emoji_id,platform_version_id,display_url,is_new,is_changed) "
                              "VALUES (%(id)s, %(emoji_id)s, %(platform_version_id)s, %(display_url)s, %(isNew)s, %(isChanged)s);")

    update_platform_version_query = ("UPDATE platform_versions SET "
                                     "prev_version_id = %(prev_version_id)s, "
                                     "release_date = %(release_date)s, "
                                     "num_emoji = %(num_emoji)s, "
                                     "num_changed_emoji = %(num_changed)s, "
                                     "num_new_emoji = %(num_new)s, "
                                     "num_removed_emoji = %(num_removed)s "
                                     "WHERE platform_version_id = %(id)s;")

    insert_emoji_query = ("INSERT INTO emoji "
                          "(emoji_id,emoji_name,emojipedia_url_ext,codepoint_string,num_codepoints,hasComponent,hasModifier,hasModifierBase,appearance_differs_flag,unicode_not_recommended) "
                          "VALUES (%(id)s, %(name)s, %(url)s, %(codepoint_string)s, %(num_codepoints)s, %(hasComponent)s, %(hasModifier)s, %(hasModifierBase)s, %(appearance_differs)s, %(not_recommended)s);")

    insert_emoji_codepoint_query = ("INSERT INTO emoji_codepoints "
                                    "(emoji_codepoint_id,emoji_id,codepoint_id,sequence_index) "
                                    "VALUES (%(id)s, %(emoji_id)s, %(codepoint_id)s, %(sequence_index)s);")

    rendering_index = 1
    emoji_to_skip = []
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
            if counts_dict is None:
                if emoji_url_ext in emoji_to_skip:
                    print('skipping {0} again'.format(emoji_url_ext))
                    print('-- skipping {0} again'.format(emoji_url_ext),file=db_file)
                    num_emoji += 1
                    continue

                # Emoji not found in dictionary, create emoji and emoji_codepoints if codepoints exist for emoji
                hasComponent = False
                hasModifier = False
                hasModifierBase = False
                emoji_codepoint_list = []
                sequence = 1
                is_emoji = True
                new_emoji = Emoji(url='/'+emoji_url_ext)
                for codepoint_U in new_emoji.codepoints:
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
                    emoji_to_skip.append(emoji_url_ext)
                    print(file=db_file)
                    print('skipping {0}, codepoint(s) not in emoji data: {1}'.format(emoji_url_ext,new_emoji.codepoints))
                    print('-- skipping {0}, codepoint(s) not in emoji data: {1}'.format(emoji_url_ext,new_emoji.codepoints),file=db_file)
                    print(file=db_file)
                    num_emoji += 1
                    continue

                # Codepoint String = straight string of codepoints: U+###U+#### (to extract, .split('U+'))
                codepoint_string = ''.join(new_emoji.codepoints)

                # Description flags for appearance differing across platforms or not being recommended by the Unicode
                description = new_emoji.description
                appearance_differs = True if "Appearance differs greatly cross-platform." in description else False
                not_recommended = True if "has not been recommended by Unicode." in description else False
                if not not_recommended:
                    not_recommended = True if "has not been Recommended For General Interchange (RGI) by Unicode." in description else False

                cur_dict = {'id':emoji_index,
                            'name':new_emoji.title,
                            'url':emoji_url_ext,
                            #'raw_character':emoji.character,
                            'codepoint_string':codepoint_string,
                            'num_codepoints':len(new_emoji.codepoints),
                            'hasComponent':hasComponent,
                            'hasModifier':hasModifier,
                            'hasModifierBase':hasModifierBase,
                            'appearance_differs':appearance_differs,
                            'not_recommended':not_recommended}
                counts_dict = {'id':emoji_index,
                               'platforms':[],
                               'num_renderings':0,
                               'num_changed_renderings':1}
                emoji_counts_dict[emoji_url_ext] = counts_dict

                print(file=db_file)
                cursor.execute(insert_emoji_query,cur_dict)
                print(cursor.statement,file=db_file)
                cursor.executemany(insert_emoji_codepoint_query,emoji_codepoint_list)
                print(cursor.statement,file=db_file)
                print(file=db_file)

                emoji_index += 1


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
            cursor.execute(insert_rendering_query,rendering_dict)
            print(cursor.statement,file=db_file)

            rendering_index += 1
            num_emoji += 1
            # if num_emoji > 5:
            #     break

        # Update platform version
        platform_version['num_emoji'] = num_emoji
        release_date_text = soup.find('div', {'class': 'content'}).findNext('ul').findNext('li').findNext('li').findNext('li').text[14:]
        release_date = dateparser.parse(release_date_text)
        platform_version['release_date'] = release_date.date()
        cursor.execute(update_platform_version_query,platform_version)
        print(cursor.statement,file=db_file)

    print(file=db_file)
    cnx.commit()
    print('- Completed -')
    print()


    # -------- rest of EMOJI --------
    print('Updating EMOJI counts')
    update_emoji_query = ("UPDATE emoji SET "
                          "num_platforms_support = %(num_platforms)s, "
                          "num_changed_renderings = %(num_changed_renderings)s, "
                          "num_renderings = %(num_renderings)s "
                          "WHERE emoji_id = %(id)s;")
    for counts in emoji_counts_dict.values():
        plat_list = counts.pop('platforms')
        counts['num_platforms'] = len(plat_list)
        cursor.execute(update_emoji_query,counts)
        print(cursor.statement,file=db_file)

    cnx.commit()
    print('- Completed -')

    print(file=db_file)
    print('COMMIT;',file=db_file)

    cnx.close()
