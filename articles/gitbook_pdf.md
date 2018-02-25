# はじめに

[GitBook](https://www.gitbook.com/)はMarkdownなどで記述したドキュメントをHTMLやPDF、EPUBなどへ変換するツールである。GitBookにはPDFを作成する機能が標準で備わっているが、それの組版のできがそれほどよくなかったので、今回はPandocとLaTeXなどを用いて美しい組版のPDFドキュメントを作成することを目指す。また、このドキュメントは[Travis CI](https://travis-ci.org/)上でコンパイルができるようにする。
この記事にある内容を行うことで、次のようなPDFが作成できる。

https://dwango.github.io/scala_text_pdf/scala_text.pdf

また、今回の成果は次のリポジトリにある。

https://github.com/dwango/scala_text_pdf

# 対象としたドキュメント

今回は[Scala Text](https://github.com/dwango/scala_text)というドキュメントのPDF版を作成することにした。このドキュメントはプログラム言語Scalaの入門テキストであるが、Markdownに埋め込まれたScalaコードを[tut](https://github.com/tpolecat/tut)というプログラムで実行していることが特徴である。

# 変換

次のような流れでPDFへ変換する。

1. [sbt](http://www.scala-sbt.org/)でtutを実行し、Scalaコードの実行結果が埋め込まれたMarkdownを生成
2. `book.json`をコピー
3. 画像ファイルをコピー
4. ソースコードをコピー
5. SVG形式の画像をInkscapeでPDFへ変換
6. PandocでLaTeXへ変換
7. LuaLaTeXで`book.json`を解析し、目次と本文を生成
8. LuaLaTeXファイルのコンパイル

この流れは、次のシェルスクリプトにまとまっている。

https://github.com/dwango/scala_text_pdf/blob/master/setup.sh

## sbtの実行

これは次のように`sbt tut`をScala Textのルートディレクトリで実行するだけでよい。

```console
$ cd ./scala_text
$ sbt tut
$ cd -
```

終了すると、`./scala_text/gitbook/`にScalaのコードを実行した結果が埋め込まれたMarkdownファイルが生成される。

## `book.json`をコピー

`book.json`とはGitBookのメタ情報を表わすJSONファイルであり、Scala Textでは次のようになっている。

```json:./scala_text/book.json
{
  "structure": {
    "readme": "INTRODUCTION.md",
    "summary": "SUMMARY.md"
  },
  "plugins": [
    "-search",
    "include-codeblock",
    "japanese-support",
    "footnote-string-to-number",
    "anchors",
    "regexplace"
  ],
  "pluginsConfig": {
    "regexplace": {
      "substitutes": [
        {"pattern": "<!-- begin answer id=\"(.*)\" style=\"(.*)\" -->", "flags": "g", "substitute": "<div><button type=\"button\" id=\"$1_show_answer_button\" style=\"display:block\" onclick=\"document.getElementById('$1').style.display='block'; document.getElementById('$1_show_answer_button').style.display='none'; document.getElementById('$1_hide_answer_button').style.display='block'; \">解答例を表示する</button><button type=\"button\" id=\"$1_hide_answer_button\" style=\"display:none\" onclick=\"document.getElementById('$1').style.display='none'; document.getElementById('$1_show_answer_button').style.display='block'; document.getElementById('$1_hide_answer_button').style.display='none'; \">解答例を隠す</button></div><div id=\"$1\" style=\"$2\">"},
        {"pattern": "<!-- end answer -->", "flags": "g", "substitute": "</div>"}
      ]
    }
  },
  "title": "Scala研修テキスト"
}
```

ここで重要なのは、目次を表わす`structure.summary`と序文を表す`structure.readme`である。この`book.json`をLaTeXファイルから読み込み、`structure.summary`にある目次ファイルを利用して本文を作成する。

## SVG形式の画像をInkscapeでPDFへ変換

LaTeXではSVG形式の画像を読み込むことができないので、[Inkscape](https://inkscape.org/ja/)を用いてPDFへ変換しそれを読み込むことにする。次のようなシェルスクリプトでSVG画像を変換する。

```bash
for f in ./img/*.svg
do
  if [[ $f =~ \./img/(.*)\.svg ]]; then
    inkscape -z -D --file=`pwd`/img/${BASH_REMATCH[1]}.svg --export-pdf=`pwd`/${BASH_REMATCH[1]}.pdf --export-latex=`pwd`/${BASH_REMATCH[1]}.pdf_tex
  fi
doneB
```

## PandocでLaTeXへ変換

GitBookのMarkdownを全て[Pandoc](http://pandoc.org/)を用いてTeXファイルへ変換する。

```bash
mkdir target
for f in ./scala_text/gitbook/*.md
do
  if [[ $f =~ \./scala_text/gitbook/(.*)\.md ]]; then
    cp $f ./target/
    pandoc -o "./target/${BASH_REMATCH[1]}.tex" -f markdown_github+footnotes+header_attributes-hard_line_breaks-intraword_underscores --latex-engine=lualatex --chapters --listings --filter=filter.py $f
  fi
done
```

まず、Pandocは多彩なMarkdown拡張に対応している。`markdown_github+footnotes+header_attributes-hard_line_breaks-intraword_underscores`というのはGitHub Markdownに追加で次のようなものを有効にする。

<dl>
  <dt>+footnote</dt>
  <dd>脚注を書ける</dd>
  <dt>+header_attributes</dt>
  <dd><code># hoge { headers }</code>のような、ヘッダ情報を書ける
  <dt>-hard_line_breaks</dt>
  <dd>改行をパラグラフの終了とみなさない</dd>
  <dt>-intraword_underscores</dt>
  <dd>単語内の<code>_</code>による強調を許可する</dd>
</dl>

また、それ以外のオプションの意味は次のようになっている。

<dl>
  <dt>--latex-engine=lualatex</dt>
  <dd>LaTeXのエンジンとしてLuaTeXを使う</dd>
  <dt>--chapters</dt>
  <dd>LaTeXのマークアップを`\chapter`からにする</dd>
  <dt>--listings</dt>
  <dd>ソースコードハイライティングにListingsを使う</dd> 
</dl>

そして、最後の`--filter=filter.py`というのは、Pandocの汎用性の高さを示す機能のひとつであると考えている。これは、ソースファイルから一旦それのASTをJSON形式で出力し、それに対して`filter`で指定したスクリプトでツリーを操作し、操作されたJSONを最終的にターゲットへ変換する、ということが可能になっている。Pandocのマニュアルから図を引用する。
http://pandoc.org/scripting.html

```text
                         source format
                              ↓
                           (pandoc)
                              ↓
                      JSON-formatted AST
                              ↓
                           (filter)
                              ↓
                      JSON-formatted AST
                              ↓
                           (pandoc)
                              ↓
                        target format
```

この`filter`では今回次のような仕事を行う。

- ListingsでScalaのスタイルを使うようにする
- GitBookのファイルのインクルード[^include]機能に対応する
- 画像がURLの場合、ダウンロードする
- 波ダッシュ`〜`（U+301C）を全角チルダ`～`（U+FF5E）へ変換する[^nami]

[^include]: GitBookはMarkdownのリンクを用いて、ファイルをインクルードする機能がある。

[^nami]: 波ダッシュはLaTeXでは意図した見た目にならない。http://www1.pm.tokushima-u.ac.jp/~kohda/tex/texlive.html

このような処理をするPythonスクリプトは次のようになる。

```python:filter.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pandocfilters import toJSONFilter, CodeBlock, RawBlock, Str, RawInline

def mkListingsEnvironment(code):
    return RawBlock('latex', "\\begin{lstlisting}[style=scala]\n" + code + "\n\\end{lstlisting}\n")

def mkInputListings(src):
    return RawInline('latex', "\\lstinputlisting[style=scala]{" + src + "}")

def mkIncludegraphics(src):
    return RawInline('latex', "\\includegraphics{img/" + src + "}")

def filter(key, value, fmt, meta):
    if key == 'CodeBlock':
        [[ident, classes, kvs], code] = value
        if 'scala' in classes:
            return mkListingsEnvironment(code)
    elif key == 'Link':
        [_, text, [href, _]] = value
        if text == [Str("include")]:
            return mkInputListings(href)
    elif key == 'Image':
        [_, _, [src, _]] = value
        if src.startswith("http"):
            fileName = src.split("/")[-1]
            os.system("cd img && curl -O " + src)
            return mkIncludegraphics(fileName)
    elif key == 'Str':
        return(Str(value.replace(u"〜", u"～")))

if __name__ == "__main__":
    toJSONFilter(filter)
```

## LuaLaTeXで`book.json`を解析し、目次と本文を生成

今回はLaTeXの処理系に[LuaTeX](https://texwiki.texjp.org/?LuaTeX)を採用したため、この部分はLuaコードで次のように実装する。よいことに、LuaTeXではJSONパーザーが提供されているのでそれを使えばよく、目次のMarkdownは簡単な形式だったので今回はやや手抜きだが正規表現で抜き出すこととした。

```lua
require("lualibs-util-jsn.lua")

local target = "./target/"
local bookJsonFile = "book.json"

function read(file)
  local handler = io.open(file, "rb")
  local content = handler:read("*all")
  handler:close()
  return content
end

function readSummary(file)
  local handler = io.open(file, "r")
  local summary = {}

  for l in handler:lines() do
    local n = string.match(l, "%[.*%]%((.*)%.md%)")
    table.insert(summary, n)
  end
  handler:close()

  return summary
end

function getTeXFile(target, name)
  return target .. name .. ".tex"
end

function getFileName(f)
  return string.match(f, "(.*)%.md")
end

local bookJson = utilities.json.tolua(read(bookJsonFile))
local readmeFile  = getTeXFile(target, getFileName(bookJson['structure']['readme']))
local summaryFile = target .. bookJson['structure']['summary']

tex.print("\\frontmatter")
tex.print("\\input{" .. readmeFile .. "}")

tex.print("\\tableofcontents")

tex.print("\\mainmatter")
for k, v in pairs(readSummary(summaryFile)) do
  tex.print("\\input{" .. getTeXFile(target, v) .. "}")
end
```

## LuaLaTeXファイルのコンパイル

LuaLaTeXファイルのコンパイルには[latexmk](https://texwiki.texjp.org/?Latexmk)とMakeを用いた。latexmkは簡単な設定ファイルを作成すると、それによって適切にLaTeXファイルをコンパイルするプログラムである。次のようなlatexmkの設定ファイルと`Makefile`を用いた。

```pl:latexmkrc
#!/usr/bin/env perl

$pdflatex = 'lualatex %O %S --interaction=nonstopmode';
$pdf_mode = 3;
$bibtex = 'pbibtex';
```

```mf:Makeflie
.PHONY : all clean

all : scala_text.pdf

clean :
	latexmk -C
	rm -r img target example_projects *.pdf *.pdf_tex book.json

scala_text.pdf :
	latexmk -pdf scala_text.tex
```

# Travis CI上によるコンパイル

さて、これらでGitBook MarkdownからPDFを作れるようになったので、Travis CI上でコンパイルできるようにする。LaTeXをTravis CI上でコンパイルすることに関しては[以前の記事](http://qiita.com/yyu/items/e3451caa86779b94abe1)を参照して欲しい。
なお、今回の`.tarivs.yml`は次のようになっている。

https://github.com/dwango/scala_text_pdf/blob/master/.travis.yml

# まとめ

このようにすることで、最終的にはある程度まともなPDFを作ることができた。もし、このPDFをよりよくする方法を思いついたり、知っていたりする場合は、この記事のコメントもしくは[Scala Text PDF](https://github.com/dwango/scala_text_pdf)のIssue、または[Scala Text](https://github.com/dwango/scala_text)のIssueのどれでもよいので、どれかで教えて欲しいと思う。

