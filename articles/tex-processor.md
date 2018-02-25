この記事は[TeX & LaTeX Advent Calendar 2013](http://www.adventar.org/calendars/187)の15日目の記事です。

- 14日目：[mskalaさん](http://ansuz.sooke.bc.ca/entry/268)
- 16日目：[PowerPC7450さん](http://qiita.com/PowerPC7450/items/b34b080dd941af689b56)

# 処理系とは

TeXの処理系とはTeXファイルをぶち込むとDVIなりPDFなりが出てくるプログラムのことです。実際に使ったことがなくても、だいたい次のようなものを聞いたことがあるのではないかと思います。

- pTeX
- XeTeX
- pdfTeX
- LuaTeX

さて、ここで疑問なのがこれらは一体何が違うのかということですね。何を使うかで迷っている人は、とりあえずこれらの違いだけでも説明出来たらいいなと。

# pTeXとその仲間たち + e-TeX

e-TeXが入っているのは、こっちの方が説明が分かりやすいと思ったからです。

## pTeX

**pTeX** はTeXに日本語向けの様々な機能を追加した処理系です。代表的なものを挙げると、次のようなものが追加されています。

- 縦書き組版
- 日本語禁則処理
- 日本語と欧文が混在した時の処理

つまり処理系を改造して日本語を扱うための機能を実装したということですね。理系の文書ではよくある日本語と欧文の混在もpTeXからサポートされていることになります。

![ptex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/ff9e9621-e184-f067-6895-409f3eaa7997.png)

## e-TeX
ところがこの時、pTeXとは別の考えでTeXを改造しようと考えた人達がいました。例えば次のような拡張です。

- レジスタ（変数的なサムシング）の上限を増加
- 新たな条件式を追加

このような拡張を積んだ新たな処理系として **e-TeX** が開発されました。こうして、TeXからフォークした処理系が二つ誕生するわけです。

![etex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/d1ced10f-871c-12c8-db4b-784dfbc31a1f.png)

TeXで文書を書く人も、レジスタを自分で定義したり何か条件式を使って組版を制御したりする人はあまりいないかもしれませんが、このような機能は複雑な組版を行う上では時々役に立ちます。

## e-pTeX

この二つの処理系（pTeXとe-TeX）をマージしようという人間が現われました。こうして二つの処理系を合体させた **e-pTeX** が誕生します。

![eptex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/90fcc696-2ee8-bf73-901c-c4f3e32c6aea.png)

ということで、現在日本語組版ではこのe-pTeXが用いられていることが多いと思います。
例えばターミナルで`platex`というコマンドを打つと、

```
This is e-pTeX, Version 3.1415926-p3.4-110825-2.6 (utf8.euc) (TeX Live 2013)
 restricted \write18 enabled.
```

などと表示されると思います。e-pTeXを使っているということですね。

## upTeX, e-upTeX

さて、これで一件落着かと思いきや、そう事は簡単ではありません。pTeXの拡張で日本語が扱えるようになったといっても、それはJIS第一・第二水準までを扱えるようになったということで、近年は常識となりつつあるUnicodeには対応していませんでした。
このままだと例えば「髙（はしごたか）」など特殊な文字や、あるいは中国語・韓国語などがうまくいかないわけです。さらに、TeXの文書ファイルをUTF-8などで書いていると不味いことになってしまうなど不自由が募ります。

そこでまず、`nkf`などを用いて入力されるTeXファイルをEUCか何かに変換して、その物体を従来のpTeXなどに捩じ込むという解決策が提案されました。
最近`platex`コマンドを使う時にはオプションとして`--kanji=utf8`を使うと思いますが、これは内側でこういう変換が行なわれています。
これでひとまずユーザーがいちいち`nkf`を使う必要はなくなりましたが、どのみち「髙」などが上手くいかない状況に変化はありません。
例えば次のようなものをe-pTeXで処理すると「髙」が亜空間へと消滅します。

```tex
\documentclass{jsarticle}

\begin{document}
「髙（はしごたか）」
\end{document}
```
![スクリーンショット 2013-12-14 17.34.12.png](https://qiita-image-store.s3.amazonaws.com/0/10815/17e18216-a38d-c6d4-abe0-90365a4757b9.png)


そこで _otf_ パッケージというものが提案され、文字コードのようなものを直接入力することでなんとかしようということになりました。こんな感じです。

```tex
\documentclass{jsarticle}
\usepackage{otf}

\begin{document}
「\UTF{9AD9}（はしごたか）」
\end{document}
```
![スクリーンショット 2013-12-14 17.34.56.png](https://qiita-image-store.s3.amazonaws.com/0/10815/c12b0d0a-1084-ae97-d8d1-011924680fba.png)


ただ、これはこれで正直微妙です。なのでpTeXを改造して、内部文字コードをUnicodeにしようという試みが行われました。これが **upTeX** です。
そうしたら後はe-TeXとのマージですね。e-TeXとマージされたものが **e-upTeX** となります。

![euptex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/5338e137-4441-686a-d7d9-da47b79a5862.png)

これらを用いると、そのまま「髙」を出力出来ます。

```tex
\documentclass[uplatex]{jsarticle}

\begin{document}
「髙（はしごたか）」
\end{document}
```
![スクリーンショット 2013-12-14 17.35.20.png](https://qiita-image-store.s3.amazonaws.com/0/10815/0009a3bf-b2dd-051d-e33e-002f9f3a7030.png)

# XeTeX

**XeTeX** もe-TeXの処理系を改造したものの一つです。

![xetex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/2aa19eca-5c52-d602-4364-f9974b1491fc.png)

XeTeXの特筆すべき機能は次のようなものです。

- Unicodeを扱える
- フォントに関する拡張

Unicodeに関する苦労は先ほどupTeXの部分で取り上げたので省略します。

XeTeXは今まで紹介した処理系とはフォントに対する処理が異なります。というのも、今までに紹介した処理系はどれも「DVIファイルを出力して、フォントに関してはDVIを処理するアプリにおまかせ」という方針でした。何故ならフォントの扱いはデバイスに依存する情報ですので、フォントを扱うというのはDVIの理念である"device independent"に反します。
ですので、e-pTeXなどではフォント埋め込みPDFを作る際は、

1. TeX側の設定（ _otf_ パッケージとかでやる）
2. dvipdfmxなどの設定（`kanji-config-updmap`とか）

という二つの手間が必要で、どうやればいいのか混乱することがままあります。
ですがXeTeXはこのデバイス非依存のDVIを生成することをそもそも諦め、デバイスに依存する代わりにデバイスで使えるフォントをそのまま使うことで面倒な設定を抜きにフォントを使用出来るようになっています。
ちなみに、XeTeXは直接PDFが生成されているように見えますが、実際は中でXDVなるDVIを拡張した形式を一旦経由して、その後 _xdvipdfmx_ というdvipdfmxを改造した物体を用いてPDFを生成しています。

XeTeXを用いた組版は[XeLaTeX で日本語する件について](http://zrbabbler.sp.land.to/xelatex.html)などで述べられていまして、日本語組版に対応しているようです。ただpTeX系と違って処理系を日本語へ特化させたというわけではないです。

# pdfTeX

これも(e-)TeXを改造した処理系で、欧文圏では高い人気があるようです。

![pdftex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/8c1bd39e-985f-370b-96e0-10532eea33ec.png)

名前の通り、これはDVIファイルを経由せずに直接PDFを吐きます。これには次のような利点があります。

- PDFを操作するための命令がTeXファイルから使える

e-pTeXなどの処理系はあくまでDVIを作ってDVIからPDFへはdvipdfmxなどに任せるというスタンスでしたが、pdfTeXはもはやDVIを作らないので、PDFに影響を与えるプリミティブな命令が用意されています。これらは例えばリンクの出力や、複雑な図の作成で効果を発揮します。

# LuaTeX

さて、 **LuaTeX** とはpdfTeXの派生で、名前にある通りLuaのコードをTeXファイルに入れることが出来ます。pdfTeXと、内部エンコーディングをUnicodeにした **Omega** という処理系の血統です。

![luatex.png](https://qiita-image-store.s3.amazonaws.com/0/10815/ebc320a6-985a-adf2-8315-cb75360710bd.png)

こちらもpTeX系とは違って処理系を直接改造して日本語化対応しているわけではありませんが、[LuaTeX-ja](http://oku.edu.mie-u.ac.jp/~okumura/texwiki/?LuaTeX-ja)など、日本語組版をがんばろうという活動が盛んに行われています。またpdfTeXの後継ということがもう決定していることもあって、将来への安心感もあります。

# まとめ

さて、色々な処理系の開発経緯が明らかになったわけですが、ここで私の独断と偏見で感想を書きます。

## pTeX系

まず、pTeX系の中ではUnicode対応などで **e-upTeX** がオススメ感があります。 _jsclasses_ など日本語組版に必要なパッケージも **e-upTeX** に対応しているので、e-upTeXがいいのではないでしょうか。
ただ私としては特に不都合がなければ、無理にe-pTeXからe-upTeXにしなくともよいと思います。

## その他

**XeTeX** か **LuaTeX** の二択だと思います。pdfTeXで日本語組版をしている話は全然聞かないです。

私はXeTeXを使っていた時がありますが、日本語組版を行う場合はzr_tex8rさんが作成した[ZXjatype](http://zrbabbler.sp.land.to/zxjatype.html)を使うことになると思います。このZXjatypeに使われている[xeCJK](http://www.ctan.org/pkg/xecjk)というパッケージがありますが、これがどうも中国語に特化しているようで、あまり日本語と仲良く出来ていない感じがあります。
ただ、XeTeXのフォントをカジュアルに使えるという点はとても素晴らしいです。なので私は変なフォントを使いたい所だけXeTeXで作って、出来あがったPDFをe-pTeXなどで読み込んだり、あるいは逆にe-pTeXなどで作ったPDFをXeTeXで読み込み加工するという方法を取っています。

ならLuaTeXなのかという話ですが、私自身はLuaTeXを全然使ったことがないので何とも言い難いです。ただ、本当にLuaが書けます。「Real World LuaTeX —Luaで書ける喜び—」ですね。
時々使う機会としては、[TikZ](http://oku.edu.mie-u.ac.jp/~okumura/texwiki/?TikZ)で図を作る時でしょうか。多分pTeX系でも問題ないと思うのですが、pdfTeX系とTikZは仲が良いらしいので、TikZで作った図をpdfTeXやLuaTeXを使ってコンパイルして、出来あがったPDFをpTeX系の処理系で読み込むといった感じの使い方をしています。
今回の記事にある各処理系の派生グラフみたいな図もTikZで作ってpdfTeXでコンパイルして、出来たPDFを`convert`コマンドでPNGに変換しています。
