#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
from pandocfilters import toJSONFilter, CodeBlock, RawBlock, Str, RawInline

def mkMathBlock(code):
    return RawBlock('html', "\\[\n" + code + "\n\\]")

def mkCodeBlock(classes, code):
    if (len(classes) == 0):
        return RawBlock('html', "<pre><code>" + code + "</code></pre>")
    else:
        return RawBlock('html', "<pre><code class=\"" + classes[0] + "\">" + code + "</code></pre>")
 
def filter(key, value, fmt, meta):
    if key == 'CodeBlock':
        [[ident, classes, kvs], code] = value
        if 'math' in classes:
            return mkMathBlock(code)
        else:
            return mkCodeBlock(classes, code)
        
if __name__ == "__main__":
    toJSONFilter(filter)
