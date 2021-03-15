import os
import sys
import string
import pdb
import argparse


#this is a primitive sentence boundary detector
#this splits sentences on period boundaries. It skips line without sentence delimiters that exceed max_sequence_length in chars. Also skips lines with less than three words
#this code needs to be changed to included additional domain specific filters


DEFAULT_MIN_WORDS = 3
DEFAULT_MAX_LENGTH=1000
DEFAULT_EXCLUDE_FILE="exclude.txt"
DEFAULT_ABBR_FILE="abbr.txt"
DEFAULT_MAX_ABBR_LENGTH=3


#Note: this script does not join lines. Line joining has to be done prior to this
sbds = [';','.','?','!','\n']


def read_lines(in_file):
    filter_list = []
    with open(in_file) as fp:
        for line in fp:
            filter_list.append(line.rstrip('\n'))
    return filter_list


def in_filter_list(filter_list,curr):
    for i in filter_list:
        if (curr.lstrip().startswith(i)):
            return True
    return False

def emit(line,params,partial_line):
    max_sequence_length = params["args"].max
    min_words = params["args"].min_words
    if (len(line) < max_sequence_length and (partial_line or len(line.split()) > min_words)):
            print(line.lstrip(),end='')


#terms like e.g. etc.
def is_abbr(curr,i,j,params):
   max_abbr_length = params["args"].abbr_length
   if (j > i and (curr[i:j+1] in params["abbrs"])):
        return True
   if (i > j or (j - i > max_abbr_length)):
        return False
   if (i == j and curr[j].isalpha()):
        return True
   orig_i = i
   while (i < j):
        if (not curr[i].isalpha() and not (curr[i] in string.punctuation)):
            return False
        i+= 1
   i = orig_i
   while (i < j):
        if (curr[i]  == '.'):
            return True
        i+= 1
   return False
        

def is_any_punct(curr,i,j):
   if (i > j):
        return False
   if (i == j and (curr[j] in string.punctuation)):
        return True
   while (i < j):
        if (curr[i] in string.punctuation):
            return True
        i += 1
   return False
        

#This checks if a terms is number 23.56 (we dont want to break on that period) or an abbrev like "Mr." which we dont want to break on either
def previous_word_abbr_or_number(curr,i,params):
    i -= 1
    if (i > 0):
        j = i
        while (j >= 0):
            if (curr[j] == ' '):
               j += 1
               break
            if (j == 0):
                break 
            else:
                j -= 1
        if (is_abbr(curr,j,i,params) or ((curr[j].isupper() and i != j and (j - i <= params["args"].abbr_length) and curr[i].islower()) or (i == j and (curr[i].islower or curr[i].isupper())))): #e. coli or Mr. Xanadu
             return True,False,j
        elif ((i == j or curr[j+1].isdigit()) and curr[i].isdigit()): #digits with currency
             return False,True,j
        else:
             return False,False,j
    else:
        return True,False,0

#This ignores period in quotes. It will break on them
def process_sbd(buffered,curr,params):
    length = len(curr)
    start = 0
    for i in range(len(curr)):
        char = curr[i]
        if (char  in sbds):
            #pdb.set_trace()
            if (i + 1 == length):
                emit(buffered + ' ' + curr[start:],params,False)
                return ""
            else:
                words = curr[i+1:].strip().split()
                if (len(words) > 0):
                    #This is a primitive sentence boundary detector. if a period is followed immediately by a space it is considered a new line except for the following character a lower case character (e. coli). So a word like EX. Coli will be broken up. E. Coli will not be broken since it is a single letter.
                    #Abbreviation like Mr. will be part of exceptions and will not be broken down
                    assert(i+1 < length)
                    is_prev_abbr,is_prev_number,prev_token_start =  previous_word_abbr_or_number(curr,i,params)
                    if (char != '.'):
                        emit(buffered + ' ' + curr[start:i+1] + '\n',params,True)
                        start = i+1
                        buffered = ''
                    elif (curr[i+1] == ' ' and is_prev_number): 
                        if (not curr[i+2].isdigit()):
                                any_punct = is_any_punct(curr,prev_token_start,i)
                                if (any_punct):
                                    end = i+1
                                else:
                                    end = prev_token_start #numbers in a line are assumed to be a bullet. Point. A downside of this is a sentence ending aith a number like 2070 will make it a new line ending with "like" and 2070 will become a new line.
                                emit(buffered + ' ' + curr[start:end] + '\n',params,True)
                                start = end
                                buffered = ''
                    elif (curr[i+1] == ' ' and not is_prev_abbr and not curr[i+2].islower()):
                        if (start == 0 and len(curr[start:i - start+1].split()) < params["args"].min_words):
                            end_char = ' '
                        else:
                            end_char = '\n'
                        emit(buffered + ' ' + curr[start:i+1] + end_char,params,True)
                        start = i+1
                        buffered = ''
                else:
                    emit(buffered + ' ' + curr[start:],params,True)
                    return ""
    return (buffered + ' ' + curr[start:]).lstrip().rstrip('\n')




def process_line(curr,buffered,nl_emitted,params):
    min_words = params["args"].min_words
    filter_list = params["exclude"]
    if (len(curr) == 1 and curr[0] == '\n'):
        if (len(buffered) > 0):
            emit(buffered + '\n',params,False)
        else:
            if (not nl_emitted):
                    print()
                    nl_emitted = True
        return "",nl_emitted
    if (len(curr.split()) <= min_words and len(buffered) == 0):
        return "",nl_emitted
    if (not in_filter_list(filter_list,curr)):
        nl_emitted = False
        buffered = process_sbd(buffered,curr,params)
    return buffered,nl_emitted


def fold_on_wb(buffer_str,max_sequence_length,min_words):
   arr = buffer_str.split()
   if (len(arr) == 1):
        pass
   else:
        curr_size = 0
        curr_str = ""
        for i in range(len(arr)):
            curr_len = len(arr[i])
            if (curr_size + curr_len + 1 >= max_sequence_length):
                emit(curr_str + '\n',max_sequence_length,False)
                curr_size = 0
                curr_str = 0
            else:
                if (curr_size == 0):
                    curr_str = arr[i]
                    curr_size += curr_len
                else:
                    curr_str += ' ' + arr[i]
                    curr_size += curr_len + 1
        if (curr_size > 0):
                emit(curr_str + '\n',max_sequence_length,min_words,False)
                
                
def collapse_spaces(line):
    ret_line = []
    is_space = False
    for ch in line:
        if (ch == ' ' or ch == '\t'):
            if (is_space):
                continue
            else:
                ret_line.append(ch)
                is_space = True
        else:
            is_space = False
            ret_line.append(ch)
    return ''.join(ret_line)



def main(params):
    file_name = params["args"].input
    max_sequence_length = params["args"].max
    single_line_doc = params["args"].single
    with open(file_name,"r") as fp:
        buffer_str = ""
        nl_emitted = False
        for line in fp:
            line = collapse_spaces(line)
            buffer_str,nl_emitted = process_line(line,buffer_str,nl_emitted,params)
            assert(len(buffer_str) == 0)
            if (len(buffer_str) > max_sequence_length):
                fold_on_wb(buffer_str,params)
                buffer_str = ''
            if (single_line_doc):
                    print()
        emit(buffer_str + '\n',params,False)
    return 0



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple sentence boundary detector - for BERT like model input ',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-input', action="store", dest="input",required=True, help='Input to file containing sentences.')
    parser.add_argument('-max', action="store", dest="max", default=DEFAULT_MAX_LENGTH,type=int,help='Maximum sentence length')
    parser.add_argument('-single', action="store", dest="single", default=False,type=bool,help='Consider each line as a document and add newline')
    parser.add_argument('-min_words', action="store", dest="min_words", default=DEFAULT_MIN_WORDS,type=int,help='Ignore lines less than this threshold of words')
    parser.add_argument('-exclude', action="store", dest="exclude", default=DEFAULT_EXCLUDE_FILE,help='Ignore these lines')
    parser.add_argument('-abbr_length', action="store", dest="abbr_length", default=DEFAULT_MAX_ABBR_LENGTH,type=int,help='Max length of abbreviations')
    parser.add_argument('-abbrs', action="store", dest="abbrs",default=DEFAULT_ABBR_FILE, help='Exception abbrs to be included regardless of abbr length')
    params = {}
    args = parser.parse_args()
    filter_list = read_lines(args.exclude)
    abbrs_list = read_lines(args.abbrs)
    params["args"] = args
    params["exclude"] = filter_list
    params["abbrs"] = abbrs_list
    main(params)
