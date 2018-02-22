# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from bs4 import BeautifulSoup
from .emoji import Emoji

import requests
from requests.adapters import HTTPAdapter

s = requests.Session()
s.mount('http', HTTPAdapter(max_retries=3))
s.mount('https', HTTPAdapter(max_retries=3))

EMOJI_CATEGORIES = ['people', 'nature', 'food-drink', 'activity',
                    'travel-places', 'objects', 'symbols', 'flags']
'''List of all valid emoji categories
'''


class Emojipedia:
    @staticmethod
    def search(query):
        '''Searches for emojis on Emojipedia. Query must be a valid emoji name.
            :param str query: the search query
            :returns: Emoji with the given name
            :rtype: Emoji
        '''
        return Emoji(Emojipedia._get_emoji_page(query))

    @staticmethod
    def random():
        '''Returns a random emoji.
            :returns: A random emoji
            :rtype: Emoji
        '''
        return Emoji(Emojipedia._get_emoji_page('random'))

    @staticmethod
    def category(query):
        '''Returns list of all emojis in the given category.
            :returns: List of emojies in the category
            :rtype: [Emoji]
        '''
        if query not in EMOJI_CATEGORIES:
            raise ValueError('{} is not a valid emoji category.'.format(query))
        soup = Emojipedia._get_page(query)
        emoji_list = soup.find('ul', {'class': 'emoji-list'})
        if not emoji_list:
            raise ValueError('Could not extract emoji list')
        emojis = []
        for emoji_entry in emoji_list.find_all('li'):
            url = emoji_entry.find('a')['href']
            emoji_text = emoji_entry.text.split(' ')
            title = ' '.join(emoji_text[1:])
            char = emoji_text[0]
            e = Emoji(url=url)
            e._title = title
            e._character = char
            emojis.append(e)
        return emojis

    """ The page emojipedia.org/emoji seems to no longer be supported! (function below is to replace)
    @staticmethod
    def all():
        '''Returns list of emojis in Emojipedia.
            An extremely powerful method.
            Returns all emojis known to human-kind. 😎
            :returns: List of all emojies
            :rtype: [Emoji]
        '''
        soup = Emojipedia._get_page('emoji')
        emoji_list = soup.find('table', {'class': 'emoji-list'})
        if not emoji_list:
            raise ValueError('Could not extract emoji list')
        emojis = []
        for emoji_entry in emoji_list.find_all('tr'):
            emoji_link = emoji_entry.find('a')
            emoji_text = emoji_link.text.split(' ')
            emoji_row, codepoints = emoji_entry.find_all('td')

            e = Emoji(url=emoji_link['href'])
            e._codepoints = codepoints.text.split(', ')
            e._character, e._title = emoji_text[0], ' '.join(emoji_text[1:])
            emojis.append(e)
        return emojis
    """

    @staticmethod
    def all_by_emoji_version(emoji_version):
        '''Returns list of emojis in Emojipedia.
            An extremely powerful method.
            Returns all emojis known to human-kind. 😎
            :returns: List of all emojies
            :rtype: [Emoji]
        '''
        soup = Emojipedia._get_page(emoji_version)

        emojis = []
        emoji_lists = soup.find('div', {'class': 'content'}).find_all('ul')
        for emoji_list in emoji_lists:
            for emoji_entry in emoji_list.find_all('li'):
                if emoji_entry.find('span', {'class': 'emoji'}):
                    emoji_link = emoji_entry.find('a')
                    emoji_text = emoji_link.text.split(' ')

                    e = Emoji(url=emoji_link['href'])
                    e._character, e._title = emoji_text[0], ' '.join(emoji_text[1:])
                    emojis.append(e)
        return emojis

    @staticmethod
    def _valid_emoji_page(soup):
        """
        (soup) -> bool
        """
        _type = soup.find('meta', {'property': 'og:type'})
        return (_type and _type['content'] == 'article')

    @staticmethod
    def _get_page(query):
        response = s.get('http://emojipedia.org/' + query)
        if response.status_code != 200:
            raise RuntimeError('Could not get emojipedia page for \'{0}\''
                               .format(query))
        return BeautifulSoup(response.text, 'html.parser')

    @staticmethod
    def _get_emoji_page(query):
        soup = Emojipedia._get_page(query)
        if not Emojipedia._valid_emoji_page(soup):
            raise ValueError('Query did not yield a emoji entry')
        return soup