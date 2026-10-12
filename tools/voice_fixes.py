"""Disambiguate voice filename parameters for the original JP parser."""
import re

VOICE = re.compile(r'<(P?V)#([A-Za-z0-9_]+)>')

def quote_voice_parameters(text):
    # JP accepts both #name and "name". Its parameter-copy routine searches
    # for a quote anywhere before falling back to '>', so a quotation in the
    # dialogue can extend an unquoted filename into the message body.
    return VOICE.sub(r'<\1"\2">', text)
