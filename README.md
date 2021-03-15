# simple_sbd
Breaks down paragraph into sentences on period char taking into account not breaking on period in numeric sequences and abbreviations. *Note this not infer a period where it is missing. BERT's MLM can be used to perform missing period detection.*

# Pre-requisites 
python 3.x

# Usage 
>> python bert_sbd.py -input test.txt > out.txt


>> python bert_sbd.py --help

```

usage: bert_sbd.py [-h] -input INPUT [-max MAX] [-single SINGLE]
                   [-min_words MIN_WORDS] [-exclude EXCLUDE]
                   [-abbr_length ABBR_LENGTH] [-abbrs ABBRS]

Simple sentence boundary detector - for BERT like model input

optional arguments:
  -h, --help            show this help message and exit
  -input INPUT          Input to file containing sentences. (default: None)
  -max MAX              Maximum sentence length (default: 1000)
  -single SINGLE        Consider each line as a document and add newline
                        (default: False)
  -min_words MIN_WORDS  Ignore lines less than this threshold of words
                        (default: 3)
  -exclude EXCLUDE      Ignore these lines (default: exclude.txt)
  -abbr_length ABBR_LENGTH
                        Max length of abbreviations (default: 3)
  -abbrs ABBRS          Exception abbrs to be included regardless of abbr
                        length (default: abbr.txt)
```



# License
MIT license
