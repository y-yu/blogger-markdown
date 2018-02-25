LaTeXで多段組は珍しいことではないが、`\section`などの見出しや表や画像などといった「本文の行の高さの整数倍ではない大きさ」が出現すると、次の画像のようにカラムのベースラインがずれてガタガタになることがままある。

![スクリーンショット 2013-12-30 22.43.18.png](https://qiita-image-store.s3.amazonaws.com/0/10815/d9775344-2f8e-39b8-92b4-792dc8934885.png)

そこでマクロを作ってこれを解決することにした。今回のマクロ作成にあたっては、[TeXでDTP ― 行位置が揃った段組](http://www.dab.hi-ho.ne.jp/t-wata/tex/multicol.html)を参考にした。

# 実装

このような、本文の行の高さの整数倍の大きさを確保することを「行取り」と言うらしい。この行取りについては、参考元のサイトに書いてあるものをほとんどそのまま用いた。
ただ、参考元のサイトにある実装では何行取るのかを著者が指定する必要があったので、そこを自動で計算するような機能を加えてみた。

## 改良したマクロ`\linespace`

マクロ`\linespace`は次の二つの使い方がある。

- `\linespace`{ _body_ }
- `\linespace`[ _number_ ]{ _body_ }

省略可能引数 _number_ を与えた場合、`\linespace`は _number_ 分の行取りを行ってそこに _body_ を挿入する。
_number_ を省略した場合、内部のマクロによって _number_ を1から順に増やしてゆき _body_ が入る最小の行取りを行う。

## 行取りの量が、改ページまでの距離より長い場合

上記のサイトの実装では次のような現象が起きる。

![スクリーンショット 2014-04-10 01.11.30.png](https://qiita-image-store.s3.amazonaws.com/0/10815/0a055133-0f79-b24c-a8b2-51ab44fd3dd8.png)

この例では箇条書きの下部がページからはみ出ているということが分かる。これについてはdoraTeXさんにより、次のような方法で解決できると教えていただいた。

<blockquote class="twitter-tweet" lang="ja"><p><a href="https://twitter.com/_yyu_">@_yyu_</a> \vtop to\z@ する前に，\ht\z@+\dp\z@ の分だけ\vspaceして，\allowbreakして再び -\ht\z@-\dp\z@ の分だけ\vspaceで戻るという手法で，ページ下余白部に\box\z@の出力があふれるのを防止できそうです。</p>&mdash; Yusuke Terada (@doraTeX) <a href="https://twitter.com/doraTeX/statuses/439406949101092864">2014, 2月 28</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

また、ZRさんから`\@linespace`の冒頭で行なっている`\noindent`によって、水平モードへ移行してしまっていて、このまま`\allowbreak`するとよくないという指摘も受けた。

<blockquote class="twitter-tweet" lang="ja"><p><a href="https://twitter.com/doraTeX">@doraTeX</a> <a href="https://twitter.com/_yyu_">@_yyu_</a> \vtop～ の箇所では水平モードになっている（冒頭の \noindent のため）ので、これだと \vspace や \allowbreak が“水平モード”の動作になります。垂直方向のペナルティを入れたいはずだと思いますが。</p>&mdash; ZR-TeXnobabbler（既定値） (@zr_tex8r) <a href="https://twitter.com/zr_tex8r/statuses/439534775863218176">2014, 2月 28</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

これについても対応した。



これで`\linespace`によってページからはみ出す問題は解決したと思う。

```tex
\makeatletter

\def\linespace{%
  \@ifnextchar[\@linespace\@linespace@auto}
\newcount\c@linespace
\long\def\@linespace@auto#1{%
  \c@linespace = 1
  \setbox\@tempboxa\vbox{#1}%
  \setlength\@tempdima{\ht\@tempboxa}%
  \addtolength\@tempdima{\dp\@tempboxa}%
  \def\@rec{%
    \setlength\@tempdimb\Cvs
    \multiply\@tempdimb\c@linespace

    \ifdim \@tempdimb>\@tempdima
      \def\@k{\@linespace[\c@linespace]{\box\@tempboxa}}%
    \else
      \advance\c@linespace1
      \def\@k{\@rec}%
    \fi
    \@k}%
  \@rec
}

\long\def\@linespace[#1]#2{%
  \par
  \setlength\@tempdima\Cvs
  \multiply\@tempdima#1
  \advance\@tempdima-\Cvs
  \advance\@tempdima-\Cht
  \advance\@tempdima\Cdp
  \setbox\z@\vbox{#2}%
  \advance\@tempdima-\ht\z@
  \advance\@tempdima-\dp\z@
  \vspace{\ht\z@}%
  \vspace{\dp\z@}%
  \allowbreak
  \vspace{-\ht\z@}%
  \vspace{-\dp\z@}%
  \vtop to\z@{%
    \vskip.5\@tempdima
    \box\z@\vss}\quad
  \setlength\@tempdima\Cvs
  \multiply\@tempdima#1
  \advance\@tempdima-2\Cvs
  \vspace\@tempdima
  \par\nobreak}

\makeatother
```

# 結果

こんな感じになる。

## _number_ を省略した場合

![スクリーンショット 2013-12-31 0.28.09.png](https://qiita-image-store.s3.amazonaws.com/0/10815/3c126a7f-f8eb-2629-06ba-b37ba055a258.png)

## _number_ を3にした場合（3行取り）

![スクリーンショット 2013-12-31 0.31.10.png](https://qiita-image-store.s3.amazonaws.com/0/10815/09271f76-6b9d-66d1-2c14-9b3c72a3f849.png)

## 大きなものを行取りしたとき

![スクリーンショット 2014-04-10 1.21.54.png](https://qiita-image-store.s3.amazonaws.com/0/10815/7924e8d9-bfbd-93d9-8d92-1531b6ec5d10.png)

このように、はみ出ないようにしてある。

# まとめ

きちんとしたものは意外と大変。

# Future Work

しばらくは問題なく使えていたが、次のような問題があると分った。

- ページ末尾に`\section`などが来たとき首吊り状態になる可能性がある
<blockquote class="twitter-tweet" lang="ja"><p><a href="https://twitter.com/_yyu_">@_yyu_</a> あと，\linespace の中身に \section などを入れたとき，それがページ末尾に来た場合にセクション見出しがいわゆる“首つり”状態になるのを防止する必要がありますね。</p>&mdash; Yusuke Terada (@doraTeX) <a href="https://twitter.com/doraTeX/statuses/439409891006873600">2014, 2月 28</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

これよりも良いものが出来たという場合は、是非おしえてください。
