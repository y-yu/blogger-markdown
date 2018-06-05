# はじめに

最近Qiitaの数式レンダリングが崩れてしまったので、一時的に数式の多い記事を[Blogger](https://www.blogger.com/)へ移すことにした。一方で、BloggerはQiitaのようにMarkdownによる投稿ができない。この記事はQiitaのMarkdownで書かれた記事をなるべくそのままPandocでHTMLへ変換しBloggerへ投稿する方法を述べる。
なお、この記事で利用したプログラムは下記のリポジトリから入手できる。

- https://github.com/y-yu/blogger-markdown

なお、この記事はQiitaとBloggerにそれぞれ投稿されている。

- Blogger: https://mentalpoker.blogspot.com/2018/02/qiitablogger.html
- Qiita: https://qiita.com/yyu/items/412529d75c2b9f89a930

# Bloggerの準備

## MathJaxの導入

Bloggerはデフォルトでは[MathJax](https://www.mathjax.org/)が使えないため、テーマを編集してMathJaxを導入する。次をテンプレートのどこかに入れればよい。

```html
<script type='text/x-mathjax-config'>
  MathJax.Hub.Config({
    extensions: [&quot;tex2jax.js&quot;],
    jax: [&quot;input/TeX&quot;, &quot;output/HTML-CSS&quot;],
    tex2jax: {
      inlineMath: [ [&#39;$&#39;,&#39;$&#39;], [&quot;\\(&quot;,&quot;\\)&quot;] ],
      displayMath: [ [&#39;$$&#39;,&#39;$$&#39;], [&quot;\\[&quot;,&quot;\\]&quot;] ],
      processEscapes: true
    },
    &quot;HTML-CSS&quot;: { availableFonts: [&quot;TeX&quot;] }
  });
</script>
<script async='' src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_CHTML' type='text/javascript'></script>
```

## highlight.jsの準備

コードハイライティングには[highlight.js](https://highlightjs.org/)を使うことにした。これもテーマに次を足せばよい。

```html
<link href='//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/styles/default.min.css' rel='stylesheet'/>
<script src='//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/highlight.min.js'/>
<script>hljs.initHighlightingOnLoad();</script>
```

## Twitter Cardsの準備

Twitter Cardsも入れたかったので、次をテーマに足した。

```html
<meta content='summary' name='twitter:card'/>
<meta content='@_yyu_' name='twitter:site'/>
<meta content='@_yyu_' name='twitter:creator'/>
<meta expr:content='data:blog.url' name='twitter:url'/>
<meta expr:content='data:blog.metaDescription' name='twitter:description'/>
<meta expr:content='data:blog.postImageThumbnailUrl' name='twitter:image'/>
<b:if cond='data:blog.pageName == &quot;&quot;'>
    <meta expr:content='data:view.title' name='twitter:text:title'/>
<b:else/>
    <meta expr:content='data:blog.pageName' name='twitter:text:title'/>
</b:if>
```

`@_yyu_`となっているところは、適宜自分のTwitter IDに置き換えてほしい。

# Pandocの準備

PandocはmacOSならば[homebrew](https://brew.sh/)から次のように導入できる。

```console
$ brew install pandoc
```

## pandocfilitersのインストール

また、[pandocfilters](https://github.com/jgm/pandocfilters)というPython製のライブラリも利用するため、pipで次のようにインストールする。

```console
$ pip install pandocfilters
```

冒頭のGitHubリポジトリを利用する場合は、[pyenv](https://github.com/pyenv/pyenv)と[virtualenv](https://github.com/pypa/virtualenv)を利用して次のようにしてもよい。

```console
$ cd /path/to/blogger-markdown/git-repository
$ pyenv virtualenv 2.7.10 blogger-markdown
$ pyenv local blogger-markdown
$ pip install -r requirements.txt
```

# Qiita記事のダウンロード

Qiitaの記事はURLの末尾に`.md`を付けることでMarkdownソースコードを得ることができる。ただし、冒頭に記事のタイトルが付与されており、これはPandocによる変換においては不要なため`sed`を利用して次のようにする。

```console
$ curl https://qiita.com/yyu/items/efcf471ce9b97e885957.md | sed -e '1d' > articles/quantum_gacha.md
```

このようにして変換元のMarkdownソースコードが得られる。

# HTMLへの変換

Pandocを利用して次のようにする。

```console
$ pandoc -f markdown_github+footnotes+header_attributes-hard_line_breaks -t html --mathjax --filter ./filters/code.py articles/guantum_gacha.md -o docs/quantum_gacha.html
```

ただし`./filters/code.py`は次のようなプログラムである。

```python:./filters/code.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
from pandocfilters import toJSONFilter, CodeBlock, RawBlock, Str, RawInline

def mkMathBlock(code):
    return RawBlock('html', "\\[\n" + code + "\n\\]")

def mkCodeBlock(classes, code):
    code = code.replace('<', '&lt;').replace('>', '&gt;')
    if (len(classes) == 0):
        return RawBlock('html', "<pre><code>" + code + "</code></pre>")
    else:
        c = (classes[0].split(':'))[0]
        return RawBlock('html', "<pre><code class=\"" + c + "\">" + code + "</code></pre>")
 
def filter(key, value, fmt, meta):
    if key == 'CodeBlock':
        [[ident, classes, kvs], code] = value
        if 'math' in classes:
            return mkMathBlock(code)
        else:
            return mkCodeBlock(classes, code)
        
if __name__ == "__main__":
    toJSONFilter(filter)
```

このプログラムは次の2つを行っている。

- コードブロックのプログラムが`math`である場合、MathJaxとしてHTMLを出力する
- コードブロックがその他である場合、プログラムとしてHTMLを出力する

このようにしてQiitaの`math`コードブロックを適切にHTMLへ変換する。

# Bloggerへの投稿

最後に出力されたHTMLをコピーして投稿する。ただし記事のタイトルは手動でQiitaから持ってくる。

# まとめ

このようにすることで、Qiitaの資産をBloggerへ移行することができる。ただ、Qiitaにはたくさんの思い出があるので数式レンダリングの不具合をなるべく早めに修正してほしい。

