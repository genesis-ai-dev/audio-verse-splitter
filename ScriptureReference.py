import requests
from functools import cache
import re
import os

book_codes = {
    'GEN': {
        'codes': ['Gen', 'Gn', '1M']
    },
    'EXO': {
        'codes': ['Ex', '2M']
    },
    'LEV': {
        'codes': ['Lev', 'Lv', '3M']
    },
    'NUM': {
        'codes': ['Nm', 'Nu', '4M']
    },
    'DEU': {
        'codes': ['Deut', 'Dt', '5M']
    },
    'JOS': {
        'codes': ['Josh', 'Jos']
    },
    'JDG': {
        'codes': ['Jdg', 'Judg']
    },
    'RUT': {
        'codes': ['Ru', 'Rth']
    },
    '1SA': {
        'codes': ['1Sam', '1Sm']
    },
    '2SA': {
        'codes': ['2Sam', '2Sm']
    },
    '1KI': {
        'codes': ['1Kg', '1K']
    },
    '2KI': {
        'codes': ['2Kg', '2K']
    },
    '1CH': {
        'codes': ['1Ch']
    },
    '2CH': {
        'codes': ['2Ch']
    },
    'EZR': {
        'codes': ['Ezr']
    },
    'NEH': {
        'codes': ['Neh']
    },
    'EST': {
        'codes': ['Est']
    },
    'JOB': {
        'codes': ['Jb', 'Job']
    },
    'PSA': {
        'codes': ['Ps']
    },
    'PRO': {
        'codes': ['Pr']
    },
    'ECC': {
        'codes': ['Ec', 'Qoh']
    },
    'SNG': {
        'codes': ['Sos', 'Song']
    },
    'ISA': {
        'codes': ['Isa']
    },
    'JER': {
        'codes': ['Jer', 'Jr']
    },
    'LAM': {
        'codes': ['Lam', 'Lm']
    },
    'EZK': {
        'codes': ['Ezek', 'Ezk']
    },
    'DAN': {
        'codes': ['Dn', 'Dan']
    },
    'HOS': {
        'codes': ['Hos', 'Hs']
    },
    'JOL': {
        'codes': ['Joel', 'Jl']
    },
    'AMO': {
        'codes': ['Am']
    },
    'OBA': {
        'codes': ['Ob']
    },
    'JON': {
        'codes': ['Jon']
    },
    'MIC': {
        'codes': ['Mi', 'Mc']
    },
    'NAM': {
        'codes': ['Na']
    },
    'HAB': {
        'codes': ['Hab']
    },
    'ZEP': {
        'codes': ['Zep', 'Zp']
    },
    'HAG': {
        'codes': ['Hag', 'Hg']
    },
    'ZEC': {
        'codes': ['Zc', 'Zec']
    },
    'MAL': {
        'codes': ['Mal', 'Ml']
    },
    'MAT': {
        'codes': ['Mt', 'Mat']
    },
    'MRK': {
        'codes': ['Mk', 'Mar']
    },
    'LUK': {
        'codes': ['Lk', 'Lu']
    },
    'JHN': {
        'codes': ['Jn', 'Joh', 'Jhn']
    },
    'ACT': {
        'codes': ['Ac']
    },
    'ROM': {
        'codes': ['Ro', 'Rm']
    },
    '1CO': {
        'codes': ['1Co']
    },
    '2CO': {
        'codes': ['2Co']
    },
    'GAL': {
        'codes': ['Gal', 'Gl']
    },
    'EPH': {
        'codes': ['Ep']
    },
    'PHP': {
        'codes': ['Php', 'Philip']
    },
    'COL': {
        'codes': ['Col']
    },
    '1TH': {
        'codes': ['1Th']
    },
    '2TH': {
        'codes': ['2Th']
    },
    '1TI': {
        'codes': ['1Ti', '1Tm']
    },
    '2TI': {
        'codes': ['2Ti', '2Tm']
    },
    'TIT': {
        'codes': ['Tit'],
    },
    'PHM': {
        'codes': ['Phile', 'Phm'],
    },
    'HEB': {
        'codes': ['Hb', 'Heb'],
    },
    'JAS': {
        'codes': ['Ja', 'Jm'],
    },
    '1PE': {
        'codes': ['1Pe', '2Pt'],
    },
    '2PE': {
        'codes': ['2Pe', '2Pt'],
    },
    '1JN': {
        'codes': ['1Jn', '1Jo', '1Jh'],
    },
    '2JN': {
        'codes': ['2Jn', '2Jo', '2Jh'],
    },
    '3JN': {
        'codes': ['3Jn', '3Jo', '3Jh'],
    },
    'JUD': {
        'codes': ['Ju', 'Jd'],
    },
    'REV': {
        'codes': ['Rev', 'Rv'],
    }
}


class ScriptureReference:
    # def __init__(self, start_ref, end_ref=None, bible_filename='eng-engwmbb'):
    #     self.start_ref = self.parse_scripture_reference(start_ref)
    #     self.end_ref = self.parse_scripture_reference(end_ref) if end_ref else self.start_ref
    #     self.bible_url = f"https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/{bible_filename}.txt"
    #     self.verses = self.get_verses_between_refs()
    def __init__(self, start_ref, end_ref=None, bible_filename='eng-engwmbb', source_type='ebible', versification='eng'):
        self.start_ref = self.parse_scripture_reference(start_ref)
        self.end_ref = self.parse_scripture_reference(end_ref) if end_ref else self.start_ref
        self.bible_filename = bible_filename
        self.source_type = source_type
        self.versification = versification
        if source_type == 'ebible':
            self.bible_url = f"https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/{bible_filename}.txt"
            self.verses = self.get_verses_between_refs()
        elif source_type == 'usfm':
            self.verses = self.extract_verses_from_usfm()

    @classmethod
    def parse_scripture_reference(cls, input_ref):
        normalized_input = re.sub(r"\s+", "", input_ref).upper()
        regex = re.compile(r"^(\d)?(\D+)(\d+)?(?::(\d+))?(?:-(\d+)?(?::(\d+))?)?$")
        match = regex.match(normalized_input)
        if not match:
            return None

        bookPrefix, bookName, startChapter, startVerse, endChapter, endVerse = match.groups()
        fullBookName = f"{bookPrefix or ''}{bookName}".upper()

        bookCode = next((code for code, details in book_codes.items() if any(fullBookName.startswith(name.upper()) for name in details['codes'])), None)
        if not bookCode:
            return None

        # Validate chapter and verse numbers by checking against the vref.txt data
        startChapter = int(startChapter) if startChapter else 1
        startVerse = int(startVerse) if startVerse else 1
        endChapter = int(endChapter) if endChapter else startChapter
        endVerse = int(endVerse) if endVerse else startVerse  # Default to the same verse if not specified

        return {
            'bookCode': bookCode,
            'startChapter': startChapter,
            'startVerse': startVerse,
            'endChapter': endChapter,
            'endVerse': endVerse
        }


    @cache
    def load_verses(self):
        # read vref lines from vref_eng.txt local file, load into verses list
        with open('vref_eng.txt', 'r') as file:
            lines = file.readlines()
            verses = [line.strip() for line in lines]


        
        # response = requests.get(f'https://raw.githubusercontent.com/BibleNLP/ebible/main/metadata/{self.versification}.vrs')
        # if response.status_code == 200:
            # lines = response.text.splitlines()
            # verses = []
            # start_processing = False
            
            # for line in lines:
            #     if line.startswith('#') or not line.strip():
            #         continue
            #     if line.startswith('GEN'):
            #         start_processing = True
            #     if start_processing:
            #         parts = line.split()
            #         book = parts[0]
            #         chapters = parts[1:]
            #         for chapter in chapters:
            #             chapter_verses = chapter.split(':')
            #             if len(chapter_verses) != 2:
            #                 continue
            #             chapter_number, verse_count = chapter_verses
            #             try:
            #                 verse_count = int(verse_count)
            #             except ValueError:
            #                 continue
            #             for verse in range(1, verse_count + 1):
            #                 verses.append(f"{book} {chapter_number}:{verse}")
            #         if line.startswith('REV'):
            #             break
           
            return verses
        # else:
        #     return []

    def load_bible_text(self):
        response = requests.get(self.bible_url)
        if response.status_code == 200:
            return response.text.splitlines()
        else:
            return []

    def get_verses_between_refs(self):
        verses = self.load_verses()
        bible_text = self.load_bible_text()
        start_index = verses.index(f"{self.start_ref['bookCode']} {self.start_ref['startChapter']}:{self.start_ref['startVerse']}")
        end_index = verses.index(f"{self.end_ref['bookCode']} {self.end_ref['endChapter']}:{self.end_ref['endVerse']}")
        return [[f"{verses[i]}".replace(' ', '_'), f"{bible_text[i]}"] for i in range(start_index, end_index + 1)]
    
    def extract_verses_from_usfm(self):
        input_directory = self.bible_filename  # Assuming bible_filename is now a directory path for USFM files
        verses = []
        files = [f for f in os.listdir(input_directory) if f.endswith('.SFM')]

        for file in files:
            input_path = os.path.join(input_directory, file)
            with open(input_path, 'r', encoding='utf-8') as infile:
                book = None
                chapter = None
                for line in infile:
                    if re.match(r'\\id (\w+)', line):
                        book = line.split()[1]
                    if re.match(r'\\c (\d+)', line):
                        chapter = line.split()[1]
                    if re.match(r'\\v (\d+)', line):
                        verse_number = line.split()[1]
                        verse_text = re.sub(r'^\\v \d+ ', '', line)
                        verse_text = re.sub(r'\\(\w+) .*?\\\1\*', '', verse_text)  # Remove tags
                        verse_text = re.sub(r'[a-zA-Z\\]+', '', verse_text)  # Remove remaining Roman characters and backslashes
                        formatted_verse = f"{book} {chapter}:{verse_number} {verse_text.strip()}"
                        formatted_verse = [f"{book}_{chapter}:{verse_number}", verse_text.strip()]
                        verses.append(formatted_verse)
        return verses

# Example usage:
# scripture_ref = ScriptureReference('lev 5:20', 'lev 5:26', "eng-engkjvcpb")
# print("Verses between references:")
# for verse in scripture_ref.verses:
#     print(verse)

# scripture_ref = ScriptureReference("rev22:20", "rev22:21", 'C:/Users/caleb/Bible Translation Project/No code/Tamazight/text', 'usfm')
# print("Verses from USFM:")
# for i, verse in enumerate(scripture_ref.verses):
#     if i < 10: 
#         print(verse)

# # Write the verses to a file
# output_path = 'C:/Users/caleb/Bible Translation Project/No code/Tamazight/text/output/verses.txt'
# with open(output_path, 'w', encoding='utf-8') as outfile:
#     for verse in scripture_ref.verses:
#         outfile.write(verse + '\n')