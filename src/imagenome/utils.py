# ----------------------------------------------------------------------------------------------------------------------
# Copyright (C) 2023 Pablo Jané
#
# imagenome is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# imagenome is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with imagenome. If not, see
# <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------------------------------------------

from time import time
from functools import wraps
from string import punctuation


def timer(s):
    """
    Decorator function that times the execution of the given input function and prints the resulting time in seconds

    :param s: initial string printed by the timer
    :type s: str
    """
    def wrap(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            print(s, end='')
            t1 = time()
            result = f(*args, **kwargs)
            t2 = time()
            print(f'Process finished successfully in {(t2-t1):.4f}s')
            return result
        return wrapped
    return wrap



def preprocess_text_tc(text):
    """
    Preprocesses input text removing leading and trailing spacing, punctuation (allowing brackets, dashes and
    percentages) and using all lowercase letters.

    :param text: input text to be preprocessed
    :type text: str
    """
    allow = ['(', ')', '[', ']', '{', '}', '-', '%']

    text = text.strip().lower()

    for char in ['\n', '\t']:
        text = text.replace(char, ' ')

    for char in punctuation:
        if char not in allow:
            text = text.replace(char, '')

    return text

