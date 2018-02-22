import mysql.connector
from local_config import db_config
from emojipedia.emojipedia import Emojipedia,EMOJI_CATEGORIES
from emoji_data import Unicode_Emoji_Data

# Connect to the database
cnx = mysql.connector.connect(user=db_config['user'],
                              host=db_config['host'],
                              password=db_config['password'],
                              database=db_config['database'])
cursor = cnx.cursor()

# Write all data definition queries to a file to be able to recreate the database without scraping
with open('database/data/insert_emoji.sql','w', encoding='utf-8') as db_file:
    print('USE emojistudy_db;',file=db_file)
    print(file=db_file)

    # -------- EMOJI VERSIONS --------
    print("Inserting EMOJI VERSIONS")
    insert_emoji_version_query = ("INSERT INTO emoji_versions "
                                  "(emoji_version_id,emoji_version,emoji_version_name,emojipedia_url_ext) "
                                  "VALUES (%(id)s, %(version)s, %(name)s, %(url)s);")
    emoji_version_list = []
    num_versions = len(Unicode_Emoji_Data.EMOJI_VERSIONS)
    emoji_version_index = 1
    for i in range(0,num_versions):
        version,name = Unicode_Emoji_Data.EMOJI_VERSIONS[i]
        version_url_ext = name.replace(' ','-').lower()
        cur_dict = {'id':emoji_version_index,
                    'version':version,
                    'name':name,
                    'url':version_url_ext}
        emoji_version_list.append(cur_dict)
        cursor.execute(insert_emoji_version_query,cur_dict)
        print(cursor.statement,file=db_file)

        emoji_version_index += 1
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
            cursor.execute(insert_codepoint_query,cur_dict)
            print(cursor.statement,file=db_file)
            codepoint_index += 1

    print(file=db_file)
    cnx.commit()
    print("- Completed -")
    print()


    # -------- EMOJI & EMOJI CODEPOINTS --------
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

    print('Getting complete list of emoji (from emoji version pages)')
    # Get all the emoji
    emoji_lists = []
    for emoji_version in emoji_version_list:
        emojis = Emojipedia.all_by_emoji_version(emoji_version["url"])
        print('Num emoji in version {0}: {1}'.format(emoji_version["name"],len(emojis)))
        emoji_lists.append((emoji_version["id"], emojis))
    print('- Completed -')
    print()


    print('Inserting EMOJI & EMOJI CODEPOINTS')
    insert_emoji_query = ("INSERT INTO emoji "
                          "(emoji_id,emoji_version_id,emoji_name,emojipedia_url_ext,emojipedia_category,codepoint_string,num_codepoints,hasComponent,hasModifier,hasModifierBase,appearance_differs_flag,unicode_not_recommended) "
                          "VALUES (%(id)s, %(version_id)s, %(name)s, %(url)s, %(category)s, %(codepoint_string)s, %(num_codepoints)s, %(hasComponent)s, %(hasModifier)s, %(hasModifierBase)s, %(appearance_differs)s, %(not_recommended)s);")

    insert_emoji_codepoint_query = ("INSERT INTO emoji_codepoints "
                                    "(emoji_codepoint_id,emoji_id,codepoint_id,sequence_index) "
                                    "VALUES (%(id)s, %(emoji_id)s, %(codepoint_id)s, %(sequence_index)s);")

    emoji_counts_dict = {}
    emoji_index = 1
    emoji_codepoint_index = 1
    for emoji_version_id,emojis in emoji_lists:
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
                        'version_id':emoji_version_id,
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

            cursor.execute(insert_emoji_query,cur_dict)
            print(cursor.statement,file=db_file)
            cursor.executemany(insert_emoji_codepoint_query,emoji_codepoint_list)
            print(cursor.statement,file=db_file)
            print(file=db_file)
            if emoji_index % 50 == 0:
                print('completed 50 emoji ({0} total so far)'.format(emoji_index))
            emoji_index += 1

    cnx.commit()
    print('- Completed - ({0} emoji inserted)'.format(emoji_index-1))
    print()

    for category in EMOJI_CATEGORIES:
        print("for category ",category,", found: ",category_count[category]['count']," out of ",category_count[category]['total'])
    print()

cnx.close()