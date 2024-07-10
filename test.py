from ScriptureReference import ScriptureReference

xhtml_dir = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'

verses = ScriptureReference('mrk 6:51', bible_filename=xhtml_dir, source_type='xhtml').verses #spa-sparvg  spa-spaRV1909

[print (verse) for verse in verses]

